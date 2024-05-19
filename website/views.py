from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import SignUpForm, AddRecordForm, AddSportForm, AddPositionForm, ProfileForm
from .models import Record, Position, UserProfile, Assessment
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views import View
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
    for assessment in assessments:
        if assessment['id'] not in [1, 2, 5, 7]:
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
            spirescore_current.append(percentile)

    spirescore_baseline = []
    for assessment in assessments:
        if assessment['id'] not in [1, 2, 5, 7]:
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

def add_battery(request):
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

def load_positions(request):
    sport_id = request.GET.get("sport")
    positions = Position.objects.filter(sport_id=sport_id)
    return render(request, "load_positions.html", {"positions": positions})


def add_sport_position(request):
    form1 = AddSportForm(request.POST, prefix='form1')
    form2 = AddPositionForm(request.POST, prefix='form2')
    if request.user.is_authenticated:
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