from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Record, Sport, Position, UserProfile, Assessment, Daily, Normative
from datetime import date
from django.utils.html import format_html

class SignUpForm(UserCreationForm):
    email = forms.EmailField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Email Address'}))
    first_name = forms.CharField(label="", max_length=50, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'First Name'}))
    last_name = forms.CharField(label="", max_length=50, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Last Name'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'User Name'
        self.fields['username'].label = ''
        self.fields['username'].help_text = '<span class="form-text text-muted"><small>Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small></span>'

        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password1'].label = ''
        self.fields['password1'].help_text = '<ul class="form-text text-muted small"><li>Your password can\'t be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can\'t be a commonly used password.</li><li>Your password can\'t be entirely numeric.</li></ul>'

        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'
        self.fields['password2'].label = ''
        self.fields['password2'].help_text = '<span class="form-text text-muted"><small>Enter the same password as before, for verification.</small></span>'	

class ProfileForm(forms.ModelForm):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('N', 'Prefer not to say')]
    sport = forms.ModelChoiceField(required=True, queryset=Sport.objects.all(), widget=forms.Select(attrs={"hx-get": "/load_positions/", "hx-target": "#id_position"}))
    position = forms.ModelChoiceField(required=False, queryset=Position.objects.none())
    bio = forms.CharField(label="", max_length=500, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Bio'}))
    birthdate = forms.DateField(label="Birthdate", widget=forms.DateInput(attrs={'class':'form-control', 'type':'date'},format='%Y-%m-%d'))
    sex = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.Select(attrs={'class':'form-control'}))

    class Meta:
        model = UserProfile
        fields = ('bio', 'sport', 'position', 'birthdate', 'sex')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['position'].queryset = Position.objects.none()
        
        if 'sport' in self.data:
            sport_id = int(self.data.get('sport'))
            self.fields['position'].queryset = Position.objects.filter(sport_id=sport_id)

class AddRecordForm(forms.ModelForm):
    profile_username = forms.CharField(required=True, widget=forms.TextInput(attrs={"placeholder": "Username", "class": "form-control"}), label="")
    assessment = forms.ModelChoiceField(required=True, queryset=Assessment.objects.all(), widget=forms.Select(attrs={'id': 'id_assessment'}))
    assessment_units = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": Assessment.units, "class": "form-control", 'id': 'id_assessment_units'}), label="Units", disabled=True)
    assessment_result = forms.CharField(required=True, widget=forms.TextInput(attrs={"placeholder": "Result", "class": "form-control"}), label="")
    assessment_notes = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "Note", "class": "form-control"}), label="")


    class Meta:
        model = Record
        fields = ('profile_username', 'assessment', 'assessment_result', 'assessment_units', 'assessment_notes', 'age')
        exclude = ("user", "profile", "age")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'assessment' in self.data:
            assessment_id = int(self.data.get('assessment'))
            assessment = Assessment.objects.get(id=assessment_id)
            self.fields['assessment_units'].initial = assessment.units

    def clean_profile_username(self):
        username = self.cleaned_data.get('profile_username')
        try:
            user_profile = UserProfile.objects.get(user__username=username)
        except UserProfile.DoesNotExist:
            raise forms.ValidationError("User with this username does not exist.")
        return user_profile

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.profile = self.cleaned_data['profile_username']

        # Calculate age based on birthdate and today's date
        birthdate = instance.profile.birthdate
        today = date.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        
        instance.age = age  # set the age

        if commit:
            instance.save()

            # Create and save a Normative instance
            normative_instance = Normative(
                assessment=instance.assessment,
                result=instance.assessment_result,
                age=instance.age
            )
            normative_instance.save()

        return instance


class AddSportForm(forms.ModelForm):
    name = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Sport Name", "class":"form-control"}), label="")

    class Meta:
        model = Sport
        exclude = ("user",)

class AddPositionForm(forms.ModelForm):
    sport = forms.ModelChoiceField(required=True, queryset=Sport.objects.all())
    name = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Position Name", "class":"form-control"}), label="")

    class Meta:
        model = Position
        exclude = ("user",)

    def clean_profile_username(self):
        username = self.cleaned_data.get('profile_username')
        try:
            user_profile = UserProfile.objects.get(user__username=username)
        except UserProfile.DoesNotExist:
            raise forms.ValidationError("User with this username does not exist.")
        return user_profile

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.profile = self.cleaned_data['profile_username']
        if commit:
            instance.save()
        return instance
    
class AddStaffForm(forms.Form):
    username = forms.CharField()

    def clean_username(self):
        username = self.cleaned_data.get('username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("User with this username does not exist.")
        return username

    def save(self):
        username = self.cleaned_data.get('username')
        user = User.objects.get(username=username)
        user.is_staff = 1
        user.save()
        return user
    
class RemoveStaffForm(forms.Form):
    username = forms.CharField()

    def clean_username(self):
        username = self.cleaned_data.get('username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("User with this username does not exist.")
        return username

    def save(self):
        username = self.cleaned_data.get('username')
        user = User.objects.get(username=username)
        user.is_staff = 0
        user.save()
        return user
    
class DateInput(forms.DateInput):
    input_type = 'date'

class ChangeDateForm(forms.Form):
    date = forms.DateField(widget=DateInput())

class SwitchWidget(forms.widgets.CheckboxInput):
    def render(self, name, value, attrs=None, renderer=None):
        # Define additional classes for the input element
        input_class = 'tgl tgl-skewed'
        if attrs is None:
            attrs = {}
        if 'class' in attrs:
            input_class += ' ' + attrs['class']
        attrs['class'] = input_class
        
        # Ensure the base class's render method is called to get the initial input element
        # This is done after modifying attrs to ensure our class is included
        checkbox_html = super().render(name, value, attrs, renderer)
        
        # Define the label's HTML, including data attributes for on/off states
        # Ensure the 'id' attribute is set in attrs to link the label to the input
        if 'id' not in attrs:
            attrs['id'] = 'id_' + name
        label_html = format_html(
            '<label class="tgl-btn" data-tg-on="Yes" data-tg-off="No" for="{}"></label>',
            attrs['id']
        )
        
        # Return the combined HTML of the input and label
        return format_html('{}{}', checkbox_html, label_html)

class RangeSliderWidget(forms.widgets.Input):
    input_type = 'range'  # Specifies that this widget is a range input

    def __init__(self, attrs=None):
        default_attrs = {'class': 'ranger', 'min': 1, 'max': 5}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

class Range3SliderWidget(forms.widgets.Input):
    input_type = 'range'  # Specifies that this widget is a range input

    def __init__(self, attrs=None):
        default_attrs = {'class': 'ranger', 'min': 0, 'max': 3}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

class DailyForm(forms.ModelForm):
    # Recovery
    soreness = forms.IntegerField(widget=RangeSliderWidget(attrs={'id': 'myRange', 'list': 'tickmarks'}), min_value=1, max_value=5, required=False)
    fatigue = forms.IntegerField(widget=RangeSliderWidget(attrs={'id': 'myRange', 'list': 'tickmarks'}), min_value=1, max_value=5, required=False)
    injury = forms.IntegerField(widget=Range3SliderWidget(attrs={'id': 'myRange', 'list': 'tickmarks'}), min_value=0, max_value=3, required=False)
    illness = forms.IntegerField(widget=Range3SliderWidget(attrs={'id': 'myRange', 'list': 'tickmarks'}), min_value=0, max_value=3, required=False)
    massage = forms.BooleanField(widget=SwitchWidget(), required=False)
    ice = forms.BooleanField(widget=SwitchWidget(), required=False)
    altitude = forms.BooleanField(widget=SwitchWidget(), required=False)
    norma_plus = forms.BooleanField(widget=SwitchWidget(), required=False)
    # Nutrition
    weight = forms.IntegerField(required=False, label='Weight (lbs)')
    hydration = forms.IntegerField(required=False, label='Hydration (Oz)')
    fruit = forms.DecimalField(required=False, label='Fruit (servings)')
    vegetable = forms.DecimalField(required=False, label='Vegetable (servings)')
    no_sweets = forms.BooleanField(widget=SwitchWidget(), required=False)
    no_alcohol = forms.BooleanField(widget=SwitchWidget(), required=False)
    beta_alanine = forms.BooleanField(widget=SwitchWidget(), required=False)
    creatine = forms.BooleanField(widget=SwitchWidget(), required=False)
    vitamin_d = forms.BooleanField(widget=SwitchWidget(), required=False)
    # Mental Training
    stress = forms.IntegerField(widget=RangeSliderWidget(attrs={'id': 'myRange', 'list': 'tickmarks'}), min_value=1, max_value=5, required=False)
    motivation = forms.IntegerField(widget=RangeSliderWidget(attrs={'id': 'myRange', 'list': 'tickmarks'}), min_value=1, max_value=5, required=False)
    read = forms.BooleanField(widget=SwitchWidget(), required=False)
    medidate = forms.BooleanField(widget=SwitchWidget(), required=False)
    visualize = forms.BooleanField(widget=SwitchWidget(), required=False)
    pray = forms.BooleanField(widget=SwitchWidget(), required=False)
    kindness = forms.BooleanField(widget=SwitchWidget(), required=False)
    be_social = forms.BooleanField(widget=SwitchWidget(), required=False)
    # Physical Training
    stretch = forms.BooleanField(widget=SwitchWidget(), required=False)
    mobility = forms.BooleanField(widget=SwitchWidget(), required=False)
    arms = forms.BooleanField(widget=SwitchWidget(), required=False)
    coordination = forms.BooleanField(widget=SwitchWidget(), required=False)
    balance = forms.BooleanField(widget=SwitchWidget(), required=False)
    speed = forms.BooleanField(widget=SwitchWidget(), required=False)
    agility = forms.BooleanField(widget=SwitchWidget(), required=False)
    strength = forms.BooleanField(widget=SwitchWidget(), required=False)
    power = forms.BooleanField(widget=SwitchWidget(), required=False)
    reaction = forms.BooleanField(widget=SwitchWidget(), required=False)
    breathwork = forms.BooleanField(widget=SwitchWidget(), required=False)
    #Notes
    notes = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={'cols': 50, 'rows': 3}))

    class Meta:
        model = Daily
        fields = ('soreness', 'fatigue', 'injury', 'illness', 'massage', 'ice', 'altitude', 'norma_plus', 'hydration', 'fruit', 'vegetable', 'weight', 'no_sweets', 'no_alcohol', 'beta_alanine', 'creatine', 'vitamin_d', 'stress', 'motivation', 'read', 'medidate', 'visualize', 'pray', 'kindness', 'be_social', 'stretch', 'mobility', 'arms', 'coordination', 'balance', 'speed', 'agility', 'strength', 'power', 'reaction', 'breathwork', 'notes')
        exclude = ('date', 'profile', 'sleep', 'sleep_score', 'bed_time', 'wake_time', 'hrv', 'rhr', 'calories_in', 'calories_out', 'carb', 'sugar', 'fiber', 'protein', 'fat', 'sat_fat', 'unsat_fat', 'omega3', 'cholesterol', 'sodium', 'potassium', 'calcium', 'iron', 'vitamin_a', 'vitamin_c', 'macro_ratio')

