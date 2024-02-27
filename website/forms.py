from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Record, Sport, Position, UserProfile

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
    sport = forms.ModelChoiceField(required=True, queryset=Sport.objects.all(), widget=forms.Select(attrs={"hx-get": "/load_positions/", "hx-target": "#id_position"}))
    position = forms.ModelChoiceField(required=False, queryset=Position.objects.none())
    bio = forms.CharField(label="", max_length=500, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Bio'}))

    class Meta:
        model = UserProfile
        fields = ('bio', 'sport', 'position')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['position'].queryset = Position.objects.none()
        
        if 'sport' in self.data:
            sport_id = int(self.data.get('sport'))
            self.fields['position'].queryset = Position.objects.filter(sport_id=sport_id)

class AddRecordForm(forms.ModelForm):
    profile_username = forms.CharField(required=True, widget=forms.TextInput(attrs={"placeholder": "Username", "class": "form-control"}), label="")
    assessment = forms.CharField(required=True, widget=forms.TextInput(attrs={"placeholder": "Assessment", "class": "form-control"}), label="")
    assessment_result = forms.CharField(required=True, widget=forms.TextInput(attrs={"placeholder": "Result", "class": "form-control"}), label="")
    assessment_units = forms.CharField(required=True, widget=forms.TextInput(attrs={"placeholder": "Units", "class": "form-control"}), label="")
    assessment_notes = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "Note", "class": "form-control"}), label="")

    class Meta:
        model = Record
        exclude = ("user", "profile")

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