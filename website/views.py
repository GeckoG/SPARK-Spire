from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import SignUpForm, AddRecordForm, AddSportForm, AddPositionForm, ProfileForm, AddStaffForm, RemoveStaffForm, DailyForm, ChangeDateForm
from .models import Record, Position, UserProfile, Assessment, Daily
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views import View
from datetime import datetime, timedelta
import json, os
import scipy.stats as stats

class GetAssessmentUnitsView(View):
    def get(self, request, *args, **kwargs):
        assessment_id = request.GET.get('assessment_id')
        print(f"Received assessment_id: {assessment_id}")  # Debugging line
        try:
            assessment = Assessment.objects.get(id=assessment_id)
            print(f"Found assessment: {assessment}")  # Debugging line
            return JsonResponse({'units': assessment.units})
        except Assessment.DoesNotExist:
            print(f"No assessment found with id: {assessment_id}")  # Debugging line
            return JsonResponse({'error': 'Invalid assessment id'}, status=400)


def home(request):
    records = Record.objects.all()
    # Check to see if logging in
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        # Authenticate
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You have been logged in!")
            return redirect('home')
        else:
            messages.success(request, "Incorrect username or password")
            return redirect('home')
    else:
        return render(request, 'home.html', {'records':records})

def profile(request, username):
    user = User.objects.get(username=username)
    profile = user.profile  # Adjust the attribute based on your model structure
    all_records = Record.objects.filter(profile=profile)

    assessments = Assessment.objects.values('id', 'name', 'units').distinct()
    assessments_requiring_min_value = [8, 9, 10]
    data = []
    for assessment in assessments:
        records = Record.objects.filter(assessment=assessment['id'], profile=profile)
        oldest = records.order_by('created_at').first()
        newest = records.order_by('-created_at').first()
        if assessment['id'] in assessments_requiring_min_value:
            extreme = records.order_by('assessment_result').first()
        else:
            extreme = records.order_by('-assessment_result').first()
        if oldest == None:
            oldest = Record(assessment_result=0, id=0)
            newest = Record(assessment_result=0, id=0)
            extreme = Record(assessment_result=0, id=0)
        data.append({
            'type': assessment['name'],
            'units': assessment['units'],
            'oldest': oldest,
            'newest': newest,
            'extreme': extreme,
        })
    
    script_dir = os.path.dirname(os.path.realpath(__file__))
    distributions_path = os.path.join(script_dir, 'distributions.json')
    with open(distributions_path, 'r') as file:
        distributions = json.load(file)

    spirescore_current = []
    # Average the grip strength and IMTP scores
    # Add the rest of the values
    for assessment in assessments:
        if assessment['id'] == 3:
            # Extract average and standard deviation for the assessment distribution
            average = distributions[assessment["name"]]["average"]
            stdev = distributions[assessment["name"]]["stdev"]

            # Given assessment value
            current_value = 0
            for item in data:
                if item['type'] == assessment["name"]:
                    current_value = item['newest'].assessment_result
                    current_value = float(current_value)
                    break

            # Calculate z-score
            z_score = (current_value - average) / stdev

            # Calculate percentile using CDF
            percentile = stats.norm.cdf(z_score) * 100
            if percentile < 0.05:
                percentile = 0
            grip_strength = percentile

        if assessment['id'] == 7:
            average = distributions[assessment["name"]]["average"]
            stdev = distributions[assessment["name"]]["stdev"]
            current_value = 0
            for item in data:
                if item['type'] == assessment["name"]:
                    current_value = item['newest'].assessment_result
                    current_value = float(current_value)
                    break
            z_score = (current_value - average) / stdev
            percentile = stats.norm.cdf(z_score) * 100
            if percentile < 0.05:
                percentile = 0
            imtp = percentile
            if grip_strength != 0:
                if imtp == 0:
                    spirescore_current.append(grip_strength)
                else:
                    average = (grip_strength + imtp) / 2
                    spirescore_current.append(average)
            else:
                spirescore_current.append(imtp)
            
        if assessment['id'] in [4, 6, 8, 9, 10]:
            average = distributions[assessment["name"]]["average"]
            stdev = distributions[assessment["name"]]["stdev"]
            current_value = 0
            for item in data:
                if item['type'] == assessment["name"]:
                    current_value = item['newest'].assessment_result
                    current_value = float(current_value)
                    break
            z_score = (current_value - average) / stdev
            percentile = stats.norm.cdf(z_score) * 100
            if current_value == 0:
                percentile = 0
            spirescore_current.append(percentile)

    print(spirescore_current)
    spirescore_baseline = []
    for assessment in assessments:
        grip_strength = 0
        imtp = 0
        if assessment['id'] == 3:
            # Extract average and standard deviation for the assessment distribution
            average = distributions[assessment["name"]]["average"]
            stdev = distributions[assessment["name"]]["stdev"]

            # Given assessment value
            baseline_value = 0
            for item in data:
                if item['type'] == assessment["name"]:
                    baseline_value = item['oldest'].assessment_result
                    baseline_value = float(baseline_value)
                    break

            # Calculate z-score
            z_score = (baseline_value - average) / stdev

            # Calculate percentile using CDF
            percentile = stats.norm.cdf(z_score) * 100
            if percentile < 0.05:
                percentile = 0
            grip_strength = percentile

        if assessment['id'] == 7:
            average = distributions[assessment["name"]]["average"]
            stdev = distributions[assessment["name"]]["stdev"]
            baseline_value = 0
            for item in data:
                if item['type'] == assessment["name"]:
                    baseline_value = item['oldest'].assessment_result
                    baseline_value = float(baseline_value)
                    break
            z_score = (baseline_value - average) / stdev
            percentile = stats.norm.cdf(z_score) * 100
            if percentile < 0.05:
                percentile = 0
            imtp = percentile
            if grip_strength != 0:
                if imtp == 0:
                    spirescore_baseline.append(grip_strength)
                else:
                    average = (grip_strength + imtp) / 2
                    spirescore_baseline.append(average)
            else:
                spirescore_baseline.append(imtp)

        if assessment['id'] in [4, 6, 8, 9, 10]:
            average = distributions[assessment["name"]]["average"]
            stdev = distributions[assessment["name"]]["stdev"]

            baseline_value = 0
            for item in data:
                if item['type'] == assessment["name"]:
                    baseline_value = item['oldest'].assessment_result
                    baseline_value = float(baseline_value)
                    break

            z_score = (baseline_value - average) / stdev

            percentile = stats.norm.cdf(z_score) * 100
            if baseline_value == 0:
                percentile = 0
            spirescore_baseline.append(percentile)

    return render(request, 'profile.html', {'profile': profile, 'records': data, 'spirescore_current': spirescore_current, 'spirescore_baseline': spirescore_baseline})



def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        # Authenticate
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You have been logged in!")
            return redirect('home')
        else:
            messages.success(request, "Incorrect username or password")
            return render(request, 'login.html')
    else:
        return render(request, 'login.html')


def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out successfully")
    return redirect('home')

def get_usernames(request):
    usernames = User.objects.values_list('username', flat=True)
    return JsonResponse(list(usernames), safe=False)

def register_user(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Authenticate & login
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "You have successfully registered!")
            return redirect('register2')
    else:
        form = SignUpForm()
        return render(request, 'register.html', {'form':form})
    return render(request, 'register.html', {'form':form})

def register_userProfile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Profile Created!")
            return redirect('home')
        else:
            print("The form did not validate")
            print(form.errors)
    else:
        form = ProfileForm()
        return render(request, 'register2.html', {'form': form})
    return render(request, 'register2.html', {'form': form})




def individual_record(request, pk):
    if request.user.is_authenticated:
        if pk == 0:
            messages.success(request, "Record does not exist")
            referer = request.META.get('HTTP_REFERER')
            # If there's a referring URL, redirect to it
            if referer is not None:
                return redirect(referer)
            # If there's no referring URL, redirect to 'home'
            else:
                return redirect('home')
        # Lookup record
        individual_record = Record.objects.get(id=pk)
        return render(request, 'record.html', {'individual_record':individual_record})
    else:
        messages.success(request, "You do not have permission to view that")
        return redirect('home')


def delete_record(request, pk):
    if request.user.is_staff:
        delete_it = Record.objects.get(id=pk)
        delete_it.delete()
        messages.success(request, "Record has been deleted")
        return redirect('home')
    else:
        messages.success(request, "You do not have permission to do that")
        return redirect('home')


def add_record(request):
    form = AddRecordForm(request.POST or None)
    if request.user.is_staff:
        if request.method == "POST":
            if form.is_valid():
                add_record = form.save()
                messages.success(request, "Record Added")
                return redirect('add_record')
        return render(request, 'add_record.html', {'form':form})
    else:
        messages.success(request, "You do not have permission to do that")
        return redirect('home')


def update_record(request, pk):
    if request.user.is_staff:
        record = Record.objects.get(pk=pk)
        if request.method == 'POST':
            form = AddRecordForm(request.POST, instance=record)
            if form.is_valid():
                form.save()
                return redirect('/record/'+str(pk))
        else:
            form = AddRecordForm(instance=record)
            form.fields['profile_username'].initial = record.profile.user.username
            return render(request, 'update_record.html', {'form':form})
    else:
        messages.success(request, "You do not have permission to do that")
        return redirect('home')

def load_positions(request):
    sport_id = request.GET.get("sport")
    positions = Position.objects.filter(sport_id=sport_id)
    return render(request, "load_positions.html", {"positions": positions})


def add_sport_position(request):
    form1 = AddSportForm(request.POST, prefix='form1')
    form2 = AddPositionForm(request.POST, prefix='form2')
    if request.user.is_staff:
        if request.method == "POST":
            if form1.is_valid():
                add_sport = form1.save()
                messages.success(request, "Sport Added")
                return redirect('add_sport_position')
            if form2.is_valid():
                add_position = form2.save()
                messages.success(request, "Position Added")
                return redirect('add_sport_position')
        return render(request, 'add_sport_position.html', {'form1':form1, 'form2':form2})
    else:
        messages.success(request, "You do not have permission to do that")
        return redirect('home')
    
def update_profile(request, username):
    user = User.objects.get(username=username)
    profile = user.profile
    if request.user == user:
        if request.method == 'POST':
            form = ProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                return redirect('/profile/'+str(username))
        else:
            form = ProfileForm(instance=profile)
            return render(request, 'update_profile.html', {'form':form})
    else:
        messages.success(request, "You cannot update another user's profile.")
        return redirect('home')
    
def add_staff(request):
    form1 = AddStaffForm(request.POST, prefix='form1')
    form2 = RemoveStaffForm(request.POST, prefix='form2')
    staff_usernames = User.objects.filter(is_staff=True).values_list('username', flat=True)
    if request.user.is_staff:
        if request.method == "POST":
            if form1.is_valid():
                add_staff = form1.save()
                messages.success(request, "User Added to Staff")
                return redirect('add_staff')
            if form2.is_valid():
                remove_staff = form2.save()
                messages.success(request, "User Removed from Staff")
                return redirect('add_staff')
        return render(request, 'add_staff.html', {'form1':form1, 'form2':form2, 'staff_usernames': staff_usernames})
    else:
        messages.success(request, "You do not have permission to do that")
        return redirect('home')
    
def daily(request, username, date):
    user = User.objects.get(username=username)
    profile = user.profile
    # Convert the date string to a date object
    date_obj = datetime.strptime(date, '%Y-%m-%d').date()  # Adjust the format '%Y-%m-%d' as needed
    
    # Calculate the day before and the day after
    day_before = date_obj - timedelta(days=1)
    day_after = date_obj + timedelta(days=1)
    
    # Convert day_before and day_after back to strings
    day_before = day_before.strftime('%Y-%m-%d')
    day_after = day_after.strftime('%Y-%m-%d')
    
    daily, created = Daily.objects.get_or_create(profile_id=profile.id, date=date_obj)
    change_date_form = None

    change_date_form = ChangeDateForm(request.POST or None)
    dailyform = DailyForm(request.POST or None, instance=daily)

    if request.method == 'POST':
        if 'change_date_submit' in request.POST:
            print("Code execution entered the change_date_submit block", flush=True)
            if change_date_form.is_valid():
                date = change_date_form.cleaned_data['date']
                # Construct the URL path and redirect
                return redirect(f'/daily/{username}/{date.strftime("%Y-%m-%d")}')
        elif 'daily_submit' in request.POST:
            print("Code execution reached the submission point")
            if dailyform.is_valid():
                print("Daily form is valid")
                try:
                    daily_instance = dailyform.save(commit=False)
                    daily_instance.profile = profile
                    daily_instance.date = date_obj
                    daily_instance.save()
                    return redirect(f'/daily/{username}/{date.strftime("%Y-%m-%d")}')
                except Exception as e:
                    print(f"Error saving daily instance: {e}")
            else:
                print(f"Daily form errors: {dailyform.errors}")
        else:
            print("Code execution reached the else block")

    # Assuming you want to use these variables in your template or further in your function
    #daily = Daily.objects.get(profile=profile, date=date_obj)
    return render(request, 'daily.html', {
        'dailyform': dailyform, 
        'day_before': day_before, 
        'day_after': day_after, 
        'date': date, 
        'change_date_form': change_date_form})

def habits(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile
    today = datetime.now()
    one_week_ago = datetime.now() - timedelta(weeks=1)
    two_weeks_ago = datetime.now() - timedelta(weeks=2)
    three_weeks_ago = datetime.now() - timedelta(weeks=3)
    four_weeks_ago = datetime.now() - timedelta(weeks=4)
    five_weeks_ago = datetime.now() - timedelta(weeks=5)
    six_weeks_ago = datetime.now() - timedelta(weeks=6)
    seven_weeks_ago = datetime.now() - timedelta(weeks=7)
    eight_weeks_ago = datetime.now() - timedelta(weeks=8)
    nine_weeks_ago = datetime.now() - timedelta(weeks=9)
    ten_weeks_ago = datetime.now() - timedelta(weeks=10)
    eleven_weeks_ago = datetime.now() - timedelta(weeks=11)
    twelve_weeks_ago = datetime.now() - timedelta(weeks=12)

    daily_entries = Daily.objects.filter(profile=profile).values('date', 'stretch', 'mobility', 'coordination', 'balance', 'speed', 'agility', 'breathwork', 'strength', 'power', 'reaction', 'stress', 'motivation', 'read', 'medidate', 'visualize', 'focus', 'kindness', 'be_social', 'sleep', 'massage', 'norma_plus', 'ice', 'altitude', 'soreness', 'fatigue', 'injury', 'illness', 'hydration', 'no_sweets', 'beta_alanine', 'creatine', 'vitamin_d', 'fruit', 'vegetable')
    last84_entries = Daily.objects.filter(profile=profile, date__gte=twelve_weeks_ago, date__lt=eleven_weeks_ago).values('date', 'stretch', 'mobility', 'coordination', 'balance', 'speed', 'agility', 'breathwork', 'strength', 'power', 'reaction', 'stress', 'motivation', 'read', 'medidate', 'visualize', 'focus', 'kindness', 'be_social', 'sleep', 'massage', 'norma_plus', 'ice', 'altitude', 'soreness', 'fatigue', 'injury', 'illness', 'hydration', 'no_sweets', 'beta_alanine', 'creatine', 'vitamin_d', 'fruit', 'vegetable')
    last77_entries = Daily.objects.filter(profile=profile, date__gte=eleven_weeks_ago, date__lt=ten_weeks_ago).values('date', 'stretch', 'mobility', 'coordination', 'balance', 'speed', 'agility', 'breathwork', 'strength', 'power', 'reaction', 'stress', 'motivation', 'read', 'medidate', 'visualize', 'focus', 'kindness', 'be_social', 'sleep', 'massage', 'norma_plus', 'ice', 'altitude', 'soreness', 'fatigue', 'injury', 'illness', 'hydration', 'no_sweets', 'beta_alanine', 'creatine', 'vitamin_d', 'fruit', 'vegetable')
    last70_entries = Daily.objects.filter(profile=profile, date__gte=ten_weeks_ago, date__lt=nine_weeks_ago).values('date', 'stretch', 'mobility', 'coordination', 'balance', 'speed', 'agility', 'breathwork', 'strength', 'power', 'reaction', 'stress', 'motivation', 'read', 'medidate', 'visualize', 'focus', 'kindness', 'be_social', 'sleep', 'massage', 'norma_plus', 'ice', 'altitude', 'soreness', 'fatigue', 'injury', 'illness', 'hydration', 'no_sweets', 'beta_alanine', 'creatine', 'vitamin_d', 'fruit', 'vegetable')
    last63_entries = Daily.objects.filter(profile=profile, date__gte=nine_weeks_ago, date__lt=eight_weeks_ago).values('date', 'stretch', 'mobility', 'coordination', 'balance', 'speed', 'agility', 'breathwork', 'strength', 'power', 'reaction', 'stress', 'motivation', 'read', 'medidate', 'visualize', 'focus', 'kindness', 'be_social', 'sleep', 'massage', 'norma_plus', 'ice', 'altitude', 'soreness', 'fatigue', 'injury', 'illness', 'hydration', 'no_sweets', 'beta_alanine', 'creatine', 'vitamin_d', 'fruit', 'vegetable')
    last56_entries = Daily.objects.filter(profile=profile, date__gte=eight_weeks_ago, date__lt=seven_weeks_ago).values('date', 'stretch', 'mobility', 'coordination', 'balance', 'speed', 'agility', 'breathwork', 'strength', 'power', 'reaction', 'stress', 'motivation', 'read', 'medidate', 'visualize', 'focus', 'kindness', 'be_social', 'sleep', 'massage', 'norma_plus', 'ice', 'altitude', 'soreness', 'fatigue', 'injury', 'illness', 'hydration', 'no_sweets', 'beta_alanine', 'creatine', 'vitamin_d', 'fruit', 'vegetable')
    last49_entries = Daily.objects.filter(profile=profile, date__gte=seven_weeks_ago, date__lt=six_weeks_ago).values('date', 'stretch', 'mobility', 'coordination', 'balance', 'speed', 'agility', 'breathwork', 'strength', 'power', 'reaction', 'stress', 'motivation', 'read', 'medidate', 'visualize', 'focus', 'kindness', 'be_social', 'sleep', 'massage', 'norma_plus', 'ice', 'altitude', 'soreness', 'fatigue', 'injury', 'illness', 'hydration', 'no_sweets', 'beta_alanine', 'creatine', 'vitamin_d', 'fruit', 'vegetable')
    last42_entries = Daily.objects.filter(profile=profile, date__gte=six_weeks_ago, date__lt=five_weeks_ago).values('date', 'stretch', 'mobility', 'coordination', 'balance', 'speed', 'agility', 'breathwork', 'strength', 'power', 'reaction', 'stress', 'motivation', 'read', 'medidate', 'visualize', 'focus', 'kindness', 'be_social', 'sleep', 'massage', 'norma_plus', 'ice', 'altitude', 'soreness', 'fatigue', 'injury', 'illness', 'hydration', 'no_sweets', 'beta_alanine', 'creatine', 'vitamin_d', 'fruit', 'vegetable')
    last35_entries = Daily.objects.filter(profile=profile, date__gte=five_weeks_ago, date__lt=four_weeks_ago).values('date', 'stretch', 'mobility', 'coordination', 'balance', 'speed', 'agility', 'breathwork', 'strength', 'power', 'reaction', 'stress', 'motivation', 'read', 'medidate', 'visualize', 'focus', 'kindness', 'be_social', 'sleep', 'massage', 'norma_plus', 'ice', 'altitude', 'soreness', 'fatigue', 'injury', 'illness', 'hydration', 'no_sweets', 'beta_alanine', 'creatine', 'vitamin_d', 'fruit', 'vegetable')
    last28_entries = Daily.objects.filter(profile=profile, date__gte=four_weeks_ago, date__lt=three_weeks_ago).values('date', 'stretch', 'mobility', 'coordination', 'balance', 'speed', 'agility', 'breathwork', 'strength', 'power', 'reaction', 'stress', 'motivation', 'read', 'medidate', 'visualize', 'focus', 'kindness', 'be_social', 'sleep', 'massage', 'norma_plus', 'ice', 'altitude', 'soreness', 'fatigue', 'injury', 'illness', 'hydration', 'no_sweets', 'beta_alanine', 'creatine', 'vitamin_d', 'fruit', 'vegetable')
    last21_entries = Daily.objects.filter(profile=profile, date__gte=three_weeks_ago, date__lt=two_weeks_ago).values('date', 'stretch', 'mobility', 'coordination', 'balance', 'speed', 'agility', 'breathwork', 'strength', 'power', 'reaction', 'stress', 'motivation', 'read', 'medidate', 'visualize', 'focus', 'kindness', 'be_social', 'sleep', 'massage', 'norma_plus', 'ice', 'altitude', 'soreness', 'fatigue', 'injury', 'illness', 'hydration', 'no_sweets', 'beta_alanine', 'creatine', 'vitamin_d', 'fruit', 'vegetable')
    last14_entries = Daily.objects.filter(profile=profile, date__gte=two_weeks_ago, date__lt=one_week_ago).values('date', 'stretch', 'mobility', 'coordination', 'balance', 'speed', 'agility', 'breathwork', 'strength', 'power', 'reaction', 'stress', 'motivation', 'read', 'medidate', 'visualize', 'focus', 'kindness', 'be_social', 'sleep', 'massage', 'norma_plus', 'ice', 'altitude', 'soreness', 'fatigue', 'injury', 'illness', 'hydration', 'no_sweets', 'beta_alanine', 'creatine', 'vitamin_d', 'fruit', 'vegetable')
    last7_entries = Daily.objects.filter(profile=profile, date__gte=one_week_ago).values('date', 'stretch', 'mobility', 'coordination', 'balance', 'speed', 'agility', 'breathwork', 'strength', 'power', 'reaction', 'stress', 'motivation', 'read', 'medidate', 'visualize', 'focus', 'kindness', 'be_social', 'sleep', 'massage', 'norma_plus', 'ice', 'altitude', 'soreness', 'fatigue', 'injury', 'illness', 'hydration', 'no_sweets', 'beta_alanine', 'creatine', 'vitamin_d', 'fruit', 'vegetable')
    today_entries = Daily.objects.filter(profile=profile, date=today).values('date', 'stretch', 'mobility', 'coordination', 'balance', 'speed', 'agility', 'breathwork', 'strength', 'power', 'reaction', 'stress', 'motivation', 'read', 'medidate', 'visualize', 'focus', 'kindness', 'be_social', 'sleep', 'massage', 'norma_plus', 'ice', 'altitude', 'soreness', 'fatigue', 'injury', 'illness', 'hydration', 'no_sweets', 'beta_alanine', 'creatine', 'vitamin_d', 'fruit', 'vegetable')

    stretch_limit = 5
    true_stretch84 = (min(sum(1 for entry in last7_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last14_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last21_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last28_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last35_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last42_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last49_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last56_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last63_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last70_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last77_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last84_entries if entry['stretch']), stretch_limit))
    true_stretch42 = (min(sum(1 for entry in last7_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last14_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last21_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last28_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last35_entries if entry['stretch']), stretch_limit)) + (min(sum(1 for entry in last42_entries if entry['stretch']), stretch_limit))
    true_stretch7 = min(sum(1 for entry in last7_entries if entry['stretch']), stretch_limit)

    mobility_limit = 5
    true_mobility84 = (min(sum(1 for entry in last7_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last14_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last21_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last28_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last35_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last42_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last49_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last56_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last63_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last70_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last77_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last84_entries if entry['mobility']), mobility_limit))
    true_mobility42 = (min(sum(1 for entry in last7_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last14_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last21_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last28_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last35_entries if entry['mobility']), mobility_limit)) + (min(sum(1 for entry in last42_entries if entry['mobility']), mobility_limit))
    true_mobility7 = min(sum(1 for entry in last7_entries if entry['mobility']), mobility_limit)

    coordination_limit = 6
    true_coordination84 = (min(sum(1 for entry in last7_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last14_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last21_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last28_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last35_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last42_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last49_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last56_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last63_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last70_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last77_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last84_entries if entry['coordination']), coordination_limit))
    true_coordination42 = (min(sum(1 for entry in last7_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last14_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last21_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last28_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last35_entries if entry['coordination']), coordination_limit)) + (min(sum(1 for entry in last42_entries if entry['coordination']), coordination_limit))
    true_coordination7 = min(sum(1 for entry in last7_entries if entry['coordination']), coordination_limit)

    balance_limit = 6
    true_balance84 = (min(sum(1 for entry in last7_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last14_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last21_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last28_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last35_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last42_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last49_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last56_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last63_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last70_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last77_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last84_entries if entry['balance']), balance_limit))
    true_balance42 = (min(sum(1 for entry in last7_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last14_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last21_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last28_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last35_entries if entry['balance']), balance_limit)) + (min(sum(1 for entry in last42_entries if entry['balance']), balance_limit))
    true_balance7 = min(sum(1 for entry in last7_entries if entry['balance']), balance_limit)

    speed_limit = 1
    true_speed84 = (min(sum(1 for entry in last7_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last14_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last21_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last28_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last35_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last42_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last49_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last56_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last63_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last70_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last77_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last84_entries if entry['speed']), speed_limit))
    true_speed42 = (min(sum(1 for entry in last7_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last14_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last21_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last28_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last35_entries if entry['speed']), speed_limit)) + (min(sum(1 for entry in last42_entries if entry['speed']), speed_limit))
    true_speed7 = min(sum(1 for entry in last7_entries if entry['speed']), speed_limit)

    agility_limit = 1
    true_agility84 = (min(sum(1 for entry in last7_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last14_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last21_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last28_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last35_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last42_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last49_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last56_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last63_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last70_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last77_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last84_entries if entry['agility']), agility_limit))
    true_agility42 = (min(sum(1 for entry in last7_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last14_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last21_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last28_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last35_entries if entry['agility']), agility_limit)) + (min(sum(1 for entry in last42_entries if entry['agility']), agility_limit))
    true_agility7 = min(sum(1 for entry in last7_entries if entry['agility']), agility_limit)

    breathwork_limit = 4
    true_breathwork84 = (min(sum(1 for entry in last7_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last14_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last21_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last28_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last35_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last42_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last49_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last56_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last63_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last70_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last77_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last84_entries if entry['breathwork']), breathwork_limit))
    true_breathwork42 = (min(sum(1 for entry in last7_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last14_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last21_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last28_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last35_entries if entry['breathwork']), breathwork_limit)) + (min(sum(1 for entry in last42_entries if entry['breathwork']), breathwork_limit))
    true_breathwork7 = min(sum(1 for entry in last7_entries if entry['breathwork']), breathwork_limit)

    strength_limit = 2
    true_strength84 = (min(sum(1 for entry in last7_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last14_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last21_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last28_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last35_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last42_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last49_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last56_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last63_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last70_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last77_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last84_entries if entry['strength']), strength_limit))
    true_strength42 = (min(sum(1 for entry in last7_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last14_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last21_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last28_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last35_entries if entry['strength']), strength_limit)) + (min(sum(1 for entry in last42_entries if entry['strength']), strength_limit))
    true_strength7 = min(sum(1 for entry in last7_entries if entry['strength']), strength_limit)

    power_limit = 1
    true_power84 = (min(sum(1 for entry in last7_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last14_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last21_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last28_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last35_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last42_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last49_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last56_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last63_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last70_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last77_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last84_entries if entry['power']), power_limit))
    true_power42 = (min(sum(1 for entry in last7_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last14_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last21_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last28_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last35_entries if entry['power']), power_limit)) + (min(sum(1 for entry in last42_entries if entry['power']), power_limit))
    true_power7 = min(sum(1 for entry in last7_entries if entry['power']), power_limit)

    reaction_limit = 2
    true_reaction84 = (min(sum(1 for entry in last7_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last14_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last21_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last28_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last35_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last42_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last49_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last56_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last63_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last70_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last77_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last84_entries if entry['reaction']), reaction_limit))
    true_reaction42 = (min(sum(1 for entry in last7_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last14_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last21_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last28_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last35_entries if entry['reaction']), reaction_limit)) + (min(sum(1 for entry in last42_entries if entry['reaction']), reaction_limit))
    true_reaction7 = min(sum(1 for entry in last7_entries if entry['reaction']), reaction_limit)

    read_limit = 4
    true_read84 = (min(sum(1 for entry in last7_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last14_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last21_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last28_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last35_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last42_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last49_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last56_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last63_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last70_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last77_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last84_entries if entry['read']), read_limit))
    true_read42 = (min(sum(1 for entry in last7_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last14_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last21_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last28_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last35_entries if entry['read']), read_limit)) + (min(sum(1 for entry in last42_entries if entry['read']), read_limit))
    true_read7 = min(sum(1 for entry in last7_entries if entry['read']), read_limit)

    medidate_limit = 2
    true_medidate84 = (min(sum(1 for entry in last7_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last14_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last21_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last28_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last35_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last42_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last49_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last56_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last63_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last70_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last77_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last84_entries if entry['medidate']), medidate_limit))
    true_medidate42 = (min(sum(1 for entry in last7_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last14_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last21_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last28_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last35_entries if entry['medidate']), medidate_limit)) + (min(sum(1 for entry in last42_entries if entry['medidate']), medidate_limit))
    true_medidate7 = min(sum(1 for entry in last7_entries if entry['medidate']), medidate_limit)

    visualize_limit = 2
    true_visualize84 = (min(sum(1 for entry in last7_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last14_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last21_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last28_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last35_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last42_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last49_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last56_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last63_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last70_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last77_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last84_entries if entry['visualize']), visualize_limit))
    true_visualize42 = (min(sum(1 for entry in last7_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last14_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last21_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last28_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last35_entries if entry['visualize']), visualize_limit)) + (min(sum(1 for entry in last42_entries if entry['visualize']), visualize_limit))
    true_visualize7 = min(sum(1 for entry in last7_entries if entry['visualize']), visualize_limit)

    focus_limit = 2
    true_focus84 = (min(sum(1 for entry in last7_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last14_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last21_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last28_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last35_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last42_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last49_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last56_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last63_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last70_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last77_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last84_entries if entry['focus']), focus_limit))
    true_focus42 = (min(sum(1 for entry in last7_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last14_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last21_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last28_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last35_entries if entry['focus']), focus_limit)) + (min(sum(1 for entry in last42_entries if entry['focus']), focus_limit))
    true_focus7 = min(sum(1 for entry in last7_entries if entry['focus']), focus_limit)

    kindness_limit = 5
    true_kindness84 = (min(sum(1 for entry in last7_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last14_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last21_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last28_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last35_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last42_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last49_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last56_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last63_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last70_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last77_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last84_entries if entry['kindness']), kindness_limit))
    true_kindness42 = (min(sum(1 for entry in last7_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last14_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last21_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last28_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last35_entries if entry['kindness']), kindness_limit)) + (min(sum(1 for entry in last42_entries if entry['kindness']), kindness_limit))
    true_kindness7 = min(sum(1 for entry in last7_entries if entry['kindness']), kindness_limit)

    be_social_limit = 5
    true_be_social84 = (min(sum(1 for entry in last7_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last14_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last21_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last28_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last35_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last42_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last49_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last56_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last63_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last70_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last77_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last84_entries if entry['be_social']), be_social_limit))
    true_be_social42 = (min(sum(1 for entry in last7_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last14_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last21_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last28_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last35_entries if entry['be_social']), be_social_limit)) + (min(sum(1 for entry in last42_entries if entry['be_social']), be_social_limit))
    true_be_social7 = min(sum(1 for entry in last7_entries if entry['be_social']), be_social_limit)

    massage_limit = 5
    true_massage84 = (min(sum(1 for entry in last7_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last14_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last21_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last28_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last35_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last42_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last49_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last56_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last63_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last70_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last77_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last84_entries if entry['massage']), massage_limit))
    true_massage42 = (min(sum(1 for entry in last7_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last14_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last21_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last28_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last35_entries if entry['massage']), massage_limit)) + (min(sum(1 for entry in last42_entries if entry['massage']), massage_limit))
    true_massage7 = min(sum(1 for entry in last7_entries if entry['massage']), massage_limit)

    norma_plus_limit = 2
    true_norma_plus84 = (min(sum(1 for entry in last7_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last14_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last21_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last28_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last35_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last42_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last49_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last56_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last63_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last70_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last77_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last84_entries if entry['norma_plus']), norma_plus_limit))
    true_norma_plus42 = (min(sum(1 for entry in last7_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last14_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last21_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last28_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last35_entries if entry['norma_plus']), norma_plus_limit)) + (min(sum(1 for entry in last42_entries if entry['norma_plus']), norma_plus_limit))
    true_norma_plus7 = min(sum(1 for entry in last7_entries if entry['norma_plus']), norma_plus_limit)

    ice_limit = 7
    true_ice84 = (min(sum(1 for entry in last7_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last14_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last21_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last28_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last35_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last42_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last49_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last56_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last63_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last70_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last77_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last84_entries if entry['ice']), ice_limit))
    true_ice42 = (min(sum(1 for entry in last7_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last14_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last21_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last28_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last35_entries if entry['ice']), ice_limit)) + (min(sum(1 for entry in last42_entries if entry['ice']), ice_limit))
    true_ice7 = min(sum(1 for entry in last7_entries if entry['ice']), ice_limit)

    altitude_limit = 7
    true_altitude84 = (min(sum(1 for entry in last7_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last14_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last21_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last28_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last35_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last42_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last49_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last56_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last63_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last70_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last77_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last84_entries if entry['altitude']), altitude_limit))
    true_altitude42 = (min(sum(1 for entry in last7_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last14_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last21_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last28_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last35_entries if entry['altitude']), altitude_limit)) + (min(sum(1 for entry in last42_entries if entry['altitude']), altitude_limit))
    true_altitude7 = min(sum(1 for entry in last7_entries if entry['altitude']), altitude_limit)

    true_beta_alanine84 = sum(1 for entry in last84_entries if entry['beta_alanine']) + sum(1 for entry in last77_entries if entry['beta_alanine']) + sum(1 for entry in last70_entries if entry['beta_alanine']) + sum(1 for entry in last63_entries if entry['beta_alanine']) + sum(1 for entry in last56_entries if entry['beta_alanine']) + sum(1 for entry in last49_entries if entry['beta_alanine']) + sum(1 for entry in last42_entries if entry['beta_alanine']) + sum(1 for entry in last35_entries if entry['beta_alanine']) + sum(1 for entry in last28_entries if entry['beta_alanine']) + sum(1 for entry in last21_entries if entry['beta_alanine']) + sum(1 for entry in last14_entries if entry['beta_alanine']) + sum(1 for entry in last7_entries if entry['beta_alanine'])
    true_beta_alanine42 = sum(1 for entry in last42_entries if entry['beta_alanine']) + sum(1 for entry in last35_entries if entry['beta_alanine']) + sum(1 for entry in last28_entries if entry['beta_alanine']) + sum(1 for entry in last21_entries if entry['beta_alanine']) + sum(1 for entry in last14_entries if entry['beta_alanine']) + sum(1 for entry in last7_entries if entry['beta_alanine'])
    true_beta_alanine7 = sum(1 for entry in last7_entries if entry['beta_alanine'])

    true_creatine84 = sum(1 for entry in last84_entries if entry['creatine']) + sum(1 for entry in last77_entries if entry['creatine']) + sum(1 for entry in last70_entries if entry['creatine']) + sum(1 for entry in last63_entries if entry['creatine']) + sum(1 for entry in last56_entries if entry['creatine']) + sum(1 for entry in last49_entries if entry['creatine']) + sum(1 for entry in last42_entries if entry['creatine']) + sum(1 for entry in last35_entries if entry['creatine']) + sum(1 for entry in last28_entries if entry['creatine']) + sum(1 for entry in last21_entries if entry['creatine']) + sum(1 for entry in last14_entries if entry['creatine']) + sum(1 for entry in last7_entries if entry['creatine'])
    true_creatine42 = sum(1 for entry in last42_entries if entry['creatine']) + sum(1 for entry in last35_entries if entry['creatine']) + sum(1 for entry in last28_entries if entry['creatine']) + sum(1 for entry in last21_entries if entry['creatine']) + sum(1 for entry in last14_entries if entry['creatine']) + sum(1 for entry in last7_entries if entry['creatine'])
    true_creatine7 = sum(1 for entry in last7_entries if entry['creatine'])

    true_vitamin_d84 = sum(1 for entry in last84_entries if entry['vitamin_d']) + sum(1 for entry in last77_entries if entry['vitamin_d']) + sum(1 for entry in last70_entries if entry['vitamin_d']) + sum(1 for entry in last63_entries if entry['vitamin_d']) + sum(1 for entry in last56_entries if entry['vitamin_d']) + sum(1 for entry in last49_entries if entry['vitamin_d']) + sum(1 for entry in last42_entries if entry['vitamin_d']) + sum(1 for entry in last35_entries if entry['vitamin_d']) + sum(1 for entry in last28_entries if entry['vitamin_d']) + sum(1 for entry in last21_entries if entry['vitamin_d']) + sum(1 for entry in last14_entries if entry['vitamin_d']) + sum(1 for entry in last7_entries if entry['vitamin_d'])
    true_vitamin_d42 = sum(1 for entry in last42_entries if entry['vitamin_d']) + sum(1 for entry in last35_entries if entry['vitamin_d']) + sum(1 for entry in last28_entries if entry['vitamin_d']) + sum(1 for entry in last21_entries if entry['vitamin_d']) + sum(1 for entry in last14_entries if entry['vitamin_d']) + sum(1 for entry in last7_entries if entry['vitamin_d'])
    true_vitamin_d7 = sum(1 for entry in last7_entries if entry['vitamin_d'])

    true_no_sweets84 = sum(1 for entry in last84_entries if entry['no_sweets']) + sum(1 for entry in last77_entries if entry['no_sweets']) + sum(1 for entry in last70_entries if entry['no_sweets']) + sum(1 for entry in last63_entries if entry['no_sweets']) + sum(1 for entry in last56_entries if entry['no_sweets']) + sum(1 for entry in last49_entries if entry['no_sweets']) + sum(1 for entry in last42_entries if entry['no_sweets']) + sum(1 for entry in last35_entries if entry['no_sweets']) + sum(1 for entry in last28_entries if entry['no_sweets']) + sum(1 for entry in last21_entries if entry['no_sweets']) + sum(1 for entry in last14_entries if entry['no_sweets']) + sum(1 for entry in last7_entries if entry['no_sweets'])
    true_no_sweets42 = sum(1 for entry in last42_entries if entry['no_sweets']) + sum(1 for entry in last35_entries if entry['no_sweets']) + sum(1 for entry in last28_entries if entry['no_sweets']) + sum(1 for entry in last21_entries if entry['no_sweets']) + sum(1 for entry in last14_entries if entry['no_sweets']) + sum(1 for entry in last7_entries if entry['no_sweets'])
    true_no_sweets7 = sum(1 for entry in last7_entries if entry['no_sweets'])

    true_hydration7 = sum(1 for entry in last7_entries if (entry['hydration'] or 0) > 99)
    true_hydration42 = (sum(1 for entry in last7_entries if (entry['hydration'] or 0) > 99) + sum(1 for entry in last14_entries if (entry['hydration'] or 0) > 99) + sum(1 for entry in last21_entries if (entry['hydration'] or 0) > 99) + sum(1 for entry in last28_entries if (entry['hydration'] or 0) > 99) + sum(1 for entry in last35_entries if (entry['hydration'] or 0) > 99) + sum(1 for entry in last42_entries if (entry['hydration'] or 0) > 99))
    true_hydration84 = (true_hydration42 + sum(1 for entry in last49_entries if (entry['hydration'] or 0) > 99) + sum(1 for entry in last56_entries if (entry['hydration'] or 0) > 99) + sum(1 for entry in last63_entries if (entry['hydration'] or 0) > 99) + sum(1 for entry in last70_entries if (entry['hydration'] or 0) > 99) + sum(1 for entry in last77_entries if (entry['hydration'] or 0) > 99) + sum(1 for entry in last84_entries if (entry['hydration'] or 0) > 99))

    true_fruit7 = sum(1 for entry in last7_entries if (entry['fruit'] or 0) > 4.9)
    true_fruit42 = ( sum(1 for entry in last7_entries if (entry['fruit'] or 0) > 4.9) + sum(1 for entry in last14_entries if (entry['fruit'] or 0) > 4.9) + sum(1 for entry in last21_entries if (entry['fruit'] or 0) > 4.9) + sum(1 for entry in last28_entries if (entry['fruit'] or 0) > 4.9) + sum(1 for entry in last35_entries if (entry['fruit'] or 0) > 4.9) + sum(1 for entry in last42_entries if (entry['fruit'] or 0) > 4.9))
    true_fruit84 = ( true_fruit42 + sum(1 for entry in last49_entries if (entry['fruit'] or 0) > 4.9) + sum(1 for entry in last56_entries if (entry['fruit'] or 0) > 4.9) + sum(1 for entry in last63_entries if (entry['fruit'] or 0) > 4.9) + sum(1 for entry in last70_entries if (entry['fruit'] or 0) > 4.9) + sum(1 for entry in last77_entries if (entry['fruit'] or 0) > 4.9) + sum(1 for entry in last84_entries if (entry['fruit'] or 0) > 4.9))

    true_vegetable7 = sum(1 for entry in last7_entries if (entry['vegetable'] or 0) > 4.9)
    true_vegetable42 = (sum(1 for entry in last7_entries if (entry['vegetable'] or 0) > 4.9) + sum(1 for entry in last14_entries if (entry['vegetable'] or 0) > 4.9) + sum(1 for entry in last21_entries if (entry['vegetable'] or 0) > 4.9) + sum(1 for entry in last28_entries if (entry['vegetable'] or 0) > 4.9) + sum(1 for entry in last35_entries if (entry['vegetable'] or 0) > 4.9) + sum(1 for entry in last42_entries if (entry['vegetable'] or 0) > 4.9))
    true_vegetable84 = (true_vegetable42 + sum(1 for entry in last49_entries if (entry['vegetable'] or 0) > 4.9) + sum(1 for entry in last56_entries if (entry['vegetable'] or 0) > 4.9) + sum(1 for entry in last63_entries if (entry['vegetable'] or 0) > 4.9) + sum(1 for entry in last70_entries if (entry['vegetable'] or 0) > 4.9) + sum(1 for entry in last77_entries if (entry['vegetable'] or 0) > 4.9) + sum(1 for entry in last84_entries if (entry['vegetable'] or 0) > 4.9))
    
    true_sleep7 = sum(1 for entry in last7_entries if (entry['sleep'] or 0) > 7.99)
    true_sleep42 = (
        sum(1 for entry in last7_entries if (entry['sleep'] or 0) > 7.99) +
        sum(1 for entry in last14_entries if (entry['sleep'] or 0) > 7.99) +
        sum(1 for entry in last21_entries if (entry['sleep'] or 0) > 7.99) +
        sum(1 for entry in last28_entries if (entry['sleep'] or 0) > 7.99) +
        sum(1 for entry in last35_entries if (entry['sleep'] or 0) > 7.99) +
        sum(1 for entry in last42_entries if (entry['sleep'] or 0) > 7.99)
    )
    true_sleep84 = (
        true_sleep42 +
        sum(1 for entry in last49_entries if (entry['sleep'] or 0) > 7.99) +
        sum(1 for entry in last56_entries if (entry['sleep'] or 0) > 7.99) +
        sum(1 for entry in last63_entries if (entry['sleep'] or 0) > 7.99) +
        sum(1 for entry in last70_entries if (entry['sleep'] or 0) > 7.99) +
        sum(1 for entry in last77_entries if (entry['sleep'] or 0) > 7.99) +
        sum(1 for entry in last84_entries if (entry['sleep'] or 0) > 7.99)
    )
    stretch_limit42 = stretch_limit * 6
    stretch_limit84 = stretch_limit * 12
    mobility_limit42 = mobility_limit * 6
    mobility_limit84 = mobility_limit * 12
    coordination_limit42 = coordination_limit * 6
    coordination_limit84 = coordination_limit * 12
    balance_limit42 = balance_limit * 6
    balance_limit84 = balance_limit * 12
    speed_limit42 = speed_limit * 6
    speed_limit84 = speed_limit * 12
    agility_limit42 = agility_limit * 6
    agility_limit84 = agility_limit * 12
    breathwork_limit42 = breathwork_limit * 6
    breathwork_limit84 = breathwork_limit * 12
    strength_limit42 = strength_limit * 6
    strength_limit84 = strength_limit * 12
    power_limit42 = power_limit * 6
    power_limit84 = power_limit * 12
    reaction_limit42 = reaction_limit * 6
    reaction_limit84 = reaction_limit * 12
    read_limit42 = read_limit * 6
    read_limit84 = read_limit * 12
    medidate_limit42 = medidate_limit * 6
    medidate_limit84 = medidate_limit * 12
    visualize_limit42 = visualize_limit * 6
    visualize_limit84 = visualize_limit * 12
    focus_limit42 = focus_limit * 6
    focus_limit84 = focus_limit * 12
    kindness_limit42 = kindness_limit * 6
    kindness_limit84 = kindness_limit * 12
    be_social_limit42 = be_social_limit * 6
    be_social_limit84 = be_social_limit * 12
    massage_limit42 = massage_limit * 6
    massage_limit84 = massage_limit * 12

    stretch_pct = round((((true_stretch7 / stretch_limit) * 0.1) + ((true_stretch42 / stretch_limit42) * 0.7) + ((true_stretch84 / stretch_limit84) * 0.2)), 2)    
    mobility_pct = round((((true_mobility7 / mobility_limit) * 0.1) + ((true_mobility42 / mobility_limit42) * 0.7) + ((true_mobility84 / mobility_limit84) * 0.2)), 2)
    coordination_pct = round((((true_coordination7 / coordination_limit) * 0.1) + ((true_coordination42 / coordination_limit42) * 0.7) + ((true_coordination84 / coordination_limit84) * 0.2)), 2)
    balance_pct = round((((true_balance7 / balance_limit) * 0.1) + ((true_balance42 / balance_limit42) * 0.7) + ((true_balance84 / balance_limit84) * 0.2)), 2)
    speed_pct = round((((true_speed7 / speed_limit) * 0.1) + ((true_speed42 / speed_limit42) * 0.7) + ((true_speed84 / speed_limit84) * 0.2)), 2)
    agility_pct = round((((true_agility7 / agility_limit) * 0.1) + ((true_agility42 / agility_limit42) * 0.7) + ((true_agility84 / agility_limit84) * 0.2)), 2)
    breathwork_pct = round((((true_breathwork7 / breathwork_limit) * 0.1) + ((true_breathwork42 / breathwork_limit42) * 0.7) + ((true_breathwork84 / breathwork_limit84) * 0.2)), 2)
    strength_pct = round((((true_strength7 / strength_limit) * 0.1) + ((true_strength42 / strength_limit42) * 0.7) + ((true_strength84 / strength_limit84) * 0.2)), 2)
    power_pct = round((((true_power7 / power_limit) * 0.1) + ((true_power42 / power_limit42) * 0.7) + ((true_power84 / power_limit84) * 0.2)), 2)
    reaction_pct = round((((true_reaction7 / reaction_limit) * 0.1) + ((true_reaction42 / reaction_limit42) * 0.7) + ((true_reaction84 / reaction_limit84) * 0.2)), 2)
    read_pct = round((((true_read7 / read_limit) * 0.1) + ((true_read42 / read_limit42) * 0.7) + ((true_read84 / read_limit84) * 0.2)), 2)
    medidate_pct = round((((true_medidate7 / medidate_limit) * 0.1) + ((true_medidate42 / medidate_limit42) * 0.7) + ((true_medidate84 / medidate_limit84) * 0.2)), 2)
    visualize_pct = round((((true_visualize7 / visualize_limit) * 0.1) + ((true_visualize42 / visualize_limit42) * 0.7) + ((true_visualize84 / visualize_limit84) * 0.2)), 2)
    focus_pct = round((((true_focus7 / focus_limit) * 0.1) + ((true_focus42 / focus_limit42) * 0.7) + ((true_focus84 / focus_limit84) * 0.2)), 2)
    kindness_pct = round((((true_kindness7 / kindness_limit) * 0.1) + ((true_kindness42 / kindness_limit42) * 0.7) + ((true_kindness84 / kindness_limit84) * 0.2)), 2)
    be_social_pct = round((((true_be_social7 / be_social_limit) * 0.1) + ((true_be_social42 / be_social_limit42) * 0.7) + ((true_be_social84 / be_social_limit84) * 0.2)), 2)
    massage_pct = round((((true_massage7 / massage_limit) * 0.1) + ((true_massage42 / massage_limit42) * 0.7) + ((true_massage84 / massage_limit84) * 0.2)), 2)
    sleep_pct = round((((true_sleep7 / 7) * 0.1) + ((true_sleep42 / 42) * 0.7) + ((true_sleep84 / 84) * 0.2)), 2)
    no_sweets_pct = round((((true_no_sweets7 / 7) * 0.1) + ((true_no_sweets42 / 42) * 0.7) + ((true_no_sweets84 / 84) * 0.2)), 2)
    hydration_pct = round((((true_hydration7 / 7) * 0.1) + ((true_hydration42 / 42) * 0.7) + ((true_hydration84 / 84) * 0.2)), 2)
    fruit_pct = round((((true_fruit7 / 7) * 0.1) + ((true_fruit42 / 42) * 0.7) + ((true_fruit84 / 84) * 0.2)), 2)
    vegetable_pct = round((((true_vegetable7 / 7) * 0.1) + ((true_vegetable42 / 42) * 0.7) + ((true_vegetable84 / 84) * 0.2)), 2)
    beta_alanine_pct = round((((true_beta_alanine7 / 7) * 0.1) + ((true_beta_alanine42 / 42) * 0.7) + ((true_beta_alanine84 / 84) * 0.2)), 2)
    creatine_pct = round((((true_creatine7 / 7) * 0.1) + ((true_creatine42 / 42) * 0.7) + ((true_creatine84 / 84) * 0.2)), 2)
    vitamin_d_pct = round((((true_vitamin_d7 / 7) * 0.1) + ((true_vitamin_d42 / 42) * 0.7) + ((true_vitamin_d84 / 84) * 0.2)), 2)
    
    soreness1 = sum(1 for entry in last7_entries if entry['soreness'] == 1)
    soreness2 = sum(1 for entry in last7_entries if entry['soreness'] == 2)
    soreness3 = sum(1 for entry in last7_entries if entry['soreness'] == 3)
    soreness_pct = today_entries[0]['soreness'] or 0
    fatigue1 = sum(1 for entry in last7_entries if entry['fatigue'] == 1)
    fatigue2 = sum(1 for entry in last7_entries if entry['fatigue'] == 2)
    fatigue3 = sum(1 for entry in last7_entries if entry['fatigue'] == 3)
    fatigue_pct = today_entries[0]['fatigue'] or 0
    illness1 = sum(1 for entry in last7_entries if entry['illness'] == 1)
    illness2 = sum(1 for entry in last7_entries if entry['illness'] == 2)
    illness3 = sum(1 for entry in last7_entries if entry['illness'] == 3)
    illness_pct = today_entries[0]['illness'] or 0
    injury1 = sum(1 for entry in last7_entries if entry['injury'] == 1)
    injury2 = sum(1 for entry in last7_entries if entry['injury'] == 2)
    injury3 = sum(1 for entry in last7_entries if entry['injury'] == 3)
    injury_pct = today_entries[0]['injury'] or 0
    stress12 = sum(1 for entry in last7_entries if entry['stress'] == 1 or entry['stress'] == 2)
    stress3 = sum(1 for entry in last7_entries if entry['stress'] == 3)
    stress45 = sum(1 for entry in last7_entries if entry['stress'] == 4 or entry['stress'] == 5)
    stress_pct = today_entries[0]['stress'] or 0
    motivation12 = sum(1 for entry in last7_entries if entry['motivation'] == 1 or entry['motivation'] == 2)
    motivation3 = sum(1 for entry in last7_entries if entry['motivation'] == 3)
    motivation45 = sum(1 for entry in last7_entries if entry['motivation'] == 4 or entry['motivation'] == 5)
    motivation_pct = today_entries[0]['motivation'] or 0

    # Convert daily_entries to a dictionary with date strings as keys and habit values as values
    daily_data = {}
    for entry in daily_entries:
        date_str = entry['date'].strftime('%Y-%m-%d')
        daily_data[date_str] = {
            'stretch': entry['stretch'],
            'mobility': entry['mobility'],
            'coordination': entry['coordination'],
            'balance': entry['balance'],
            'speed': entry['speed'],
            'agility': entry['agility'],
            'breathwork': entry['breathwork'],
            'strength': entry['strength'],
            'power': entry['power'],
            'reaction': entry['reaction'],
            'read': entry['read'],
            'medidate': entry['medidate'],
            'visualize': entry['visualize'],
            'focus': entry['focus'],
            'kindness': entry['kindness'],
            'be_social': entry['be_social'],
            'sleep': entry['sleep'],
            'massage': entry['massage'],
            'norma_plus': entry['norma_plus'],
            'ice': entry['ice'],
            'altitude': entry['altitude'],
            'soreness': entry['soreness'],
            'fatigue': entry['fatigue'],
            'illness': entry['illness'],
            'injury': entry['injury'],
            'hydration': entry['hydration'],
            'no_sweets': entry['no_sweets'],
            'beta_alanine': entry['beta_alanine'],
            'creatine': entry['creatine'],
            'vitamin_d': entry['vitamin_d'],
            'fruit': entry['fruit'],
            'vegetable': entry['vegetable']
        }

    return render(request, 'habits.html', {
        'stretch_pct': stretch_pct, 'stretch_limit': stretch_limit, 'stretch_limit42': stretch_limit42, 'stretch_limit84': stretch_limit84, 'true_stretch7': true_stretch7, 'true_stretch42': true_stretch42, 'true_stretch84': true_stretch84, 'stretch_label': "Stretch",
        'mobility_pct': mobility_pct, 'mobility_limit': mobility_limit, 'mobility_limit42': mobility_limit42, 'mobility_limit84': mobility_limit84, 'true_mobility7': true_mobility7, 'true_mobility42': true_mobility42, 'true_mobility84': true_mobility84, 'mobility_label': "Mobility",
        'coordination_pct': coordination_pct, 'coordination_limit': coordination_limit, 'coordination_limit42': coordination_limit42, 'coordination_limit84': coordination_limit84, 'true_coordination7': true_coordination7, 'true_coordination42': true_coordination42, 'true_coordination84': true_coordination84, 'coordination_label': "Coordination",
        'balance_pct': balance_pct, 'balance_limit': balance_limit, 'balance_limit42': balance_limit42, 'balance_limit84': balance_limit84, 'true_balance7': true_balance7, 'true_balance42': true_balance42, 'true_balance84': true_balance84, 'balance_label': "Balance",
        'speed_pct': speed_pct, 'speed_limit': speed_limit, 'speed_limit42': speed_limit42, 'speed_limit84': speed_limit84, 'true_speed7': true_speed7, 'true_speed42': true_speed42, 'true_speed84': true_speed84, 'speed_label': "Speed",
        'agility_pct': agility_pct, 'agility_limit': agility_limit, 'agility_limit42': agility_limit42, 'agility_limit84': agility_limit84, 'true_agility7': true_agility7, 'true_agility42': true_agility42, 'true_agility84': true_agility84, 'agility_label': "Agility",
        'breathwork_pct': breathwork_pct, 'breathwork_limit': breathwork_limit, 'breathwork_limit42': breathwork_limit42, 'breathwork_limit84': breathwork_limit84, 'true_breathwork7': true_breathwork7, 'true_breathwork42': true_breathwork42, 'true_breathwork84': true_breathwork84, 'breathwork_label': "Breathwork",
        'strength_pct': strength_pct, 'strength_limit': strength_limit, 'strength_limit42': strength_limit42, 'strength_limit84': strength_limit84, 'true_strength7': true_strength7, 'true_strength42': true_strength42, 'true_strength84': true_strength84, 'strength_label': "Strength",
        'power_pct': power_pct, 'power_limit': power_limit, 'power_limit42': power_limit42, 'power_limit84': power_limit84, 'true_power7': true_power7, 'true_power42': true_power42, 'true_power84': true_power84, 'power_label': "Power",
        'reaction_pct': reaction_pct, 'reaction_limit': reaction_limit, 'reaction_limit42': reaction_limit42, 'reaction_limit84': reaction_limit84, 'true_reaction7': true_reaction7, 'true_reaction42': true_reaction42, 'true_reaction84': true_reaction84, 'reaction_label': "Reaction",
        
        'stress_pct': stress_pct, 'stress12': stress12, 'stress3': stress3, 'stress45': stress45, 'stress_label': "Stress",
        'motivation_pct': motivation_pct, 'motivation12': motivation12, 'motivation3': motivation3, 'motivation45': motivation45, 'motivation_label': "Motivation",
        'read_pct': read_pct, 'read_limit': read_limit, 'read_limit42': read_limit42, 'read_limit84': read_limit84, 'true_read7': true_read7, 'true_read42': true_read42, 'true_read84': true_read84, 'read_label': "Read",
        'medidate_pct': medidate_pct, 'medidate_limit': medidate_limit, 'medidate_limit42': medidate_limit42, 'medidate_limit84': medidate_limit84, 'true_medidate7': true_medidate7, 'true_medidate42': true_medidate42, 'true_medidate84': true_medidate84, 'medidate_label': "Meditate",
        'visualize_pct': visualize_pct, 'visualize_limit': visualize_limit, 'visualize_limit42': visualize_limit42, 'visualize_limit84': visualize_limit84, 'true_visualize7': true_visualize7, 'true_visualize42': true_visualize42, 'true_visualize84': true_visualize84, 'visualize_label': "Visualize",
        'focus_pct': focus_pct, 'focus_limit': focus_limit, 'focus_limit42': focus_limit42, 'focus_limit84': focus_limit84, 'true_focus7': true_focus7, 'true_focus42': true_focus42, 'true_focus84': true_focus84, 'focus_label': "Focus",
        'kindness_pct': kindness_pct, 'kindness_limit': kindness_limit, 'kindness_limit42': kindness_limit42, 'kindness_limit84': kindness_limit84, 'true_kindness7': true_kindness7, 'true_kindness42': true_kindness42, 'true_kindness84': true_kindness84, 'kindness_label': "Kindness",
        'be_social_pct': be_social_pct, 'be_social_limit': be_social_limit, 'be_social_limit42': be_social_limit42, 'be_social_limit84': be_social_limit84, 'true_be_social7': true_be_social7, 'true_be_social42': true_be_social42, 'true_be_social84': true_be_social84, 'be_social_label': "Socialize",
        
        'sleep_pct': sleep_pct, 'true_sleep7': true_sleep7, 'true_sleep42': true_sleep42, 'true_sleep84': true_sleep84, 'sleep_label': "Sleep",
        'massage_pct': massage_pct, 'massage_limit': massage_limit, 'massage_limit42': massage_limit42, 'massage_limit84': massage_limit84, 'true_massage7': true_massage7, 'true_massage42': true_massage42, 'true_massage84': true_massage84, 'massage_label': "Massage",
        'true_norma_plus7': true_norma_plus7, 'true_norma_plus42': true_norma_plus42, 'true_norma_plus84': true_norma_plus84, 'norma_plus_label': "Norma Plus",
        'true_ice7': true_ice7, 'true_ice42': true_ice42, 'true_ice84': true_ice84, 'ice_label': "Ice",
        'true_altitude7': true_altitude7, 'true_altitude42': true_altitude42, 'true_altitude84': true_altitude84, 'altitude_label': "Altitude",
        'soreness_pct': soreness_pct, 'soreness1': soreness1, 'soreness2': soreness2, 'soreness3': soreness3,
        'fatigue_pct': fatigue_pct, 'fatigue1': fatigue1, 'fatigue2': fatigue2, 'fatigue3': fatigue3,
        'illness_pct': illness_pct, 'illness1': illness1, 'illness2': illness2, 'illness3': illness3,
        'injury_pct': injury_pct, 'injury1': injury1, 'injury2': injury2, 'injury3': injury3,
        
        'hydration_pct': hydration_pct, 'true_hydration7': true_hydration7, 'true_hydration42': true_hydration42, 'true_hydration84': true_hydration84, 'hydration_label': "Hydration",
        'no_sweets_pct': no_sweets_pct, 'true_no_sweets7': true_no_sweets7, 'true_no_sweets42': true_no_sweets42, 'true_no_sweets84': true_no_sweets84, 'no_sweets_label': "No Sweets",
        'beta_alanine_pct': beta_alanine_pct, 'true_beta_alanine7': true_beta_alanine7, 'true_beta_alanine42': true_beta_alanine42, 'true_beta_alanine84': true_beta_alanine84, 'beta_alanine_label': "B Alanine",
        'creatine_pct': creatine_pct, 'true_creatine7': true_creatine7, 'true_creatine42': true_creatine42, 'true_creatine84': true_creatine84, 'creatine_label': "Creatine",
        'vitamin_d_pct': vitamin_d_pct, 'true_vitamin_d7': true_vitamin_d7, 'true_vitamin_d42': true_vitamin_d42, 'true_vitamin_d84': true_vitamin_d84, 'vitamin_d_label': "Vitamin D",
        'fruit_pct': fruit_pct, 'true_fruit7': true_fruit7, 'true_fruit42': true_fruit42, 'true_fruit84': true_fruit84, 'fruit_label': "Fruits",
        'vegetable_pct': vegetable_pct, 'true_vegetable7': true_vegetable7, 'true_vegetable42': true_vegetable42, 'true_vegetable84': true_vegetable84, 'vegetable_label': "Veggies",
                
        'daily_data': json.dumps(daily_data)  # Serialize to JSON so we don't get an error when reading True False with capital letters (javascript needs all-lowercase)
    })