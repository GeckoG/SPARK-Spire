from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import SignUpForm, AddRecordForm, AddSportForm, AddPositionForm, ProfileForm
from .models import Record, Position, UserProfile

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
    profile = user.userprofile  # Adjust the attribute based on your model structure
    return render(request, 'profile.html', {'profile': profile})

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
            return redirect('home')
    else:
        return render(request, 'login.html')


def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out successfully")
    return redirect('home')


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
        # Lookup record
        individual_record = Record.objects.get(id=pk)
        return render(request, 'record.html', {'individual_record':individual_record})
    else:
        messages.success(request, "You do not have permission to view that")
        return redirect('home')


def delete_record(request, pk):
    if request.user.is_authenticated:
        delete_it = Record.objects.get(id=pk)
        delete_it.delete()
        messages.success(request, "Record has been deleted")
        return redirect('home')
    else:
        messages.success(request, "You do not have permission to do that")
        return redirect('home')


def add_record(request):
    form = AddRecordForm(request.POST or None)
    if request.user.is_authenticated:
        if request.method == "POST":
            if form.is_valid():
                add_record = form.save()
                messages.success(request, "Record Added")
                return redirect('home')
        return render(request, 'add_record.html', {'form':form})
    else:
        messages.success(request, "You do not have permission to do that")
        return redirect('home')


def update_record(request, pk):
    if request.user.is_authenticated:
        current_record = Record.objects.get(id=pk)
        form = AddRecordForm(request.POST or None, instance=current_record)
        if form.is_valid():
            form.save()
            messages.info(request, "Record has been updated!")
            newthing = str(current_record.id)
            return redirect('/record/' + newthing)
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