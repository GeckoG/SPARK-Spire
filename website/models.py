from django.contrib.auth.models import User
from django.db import models


class Sport(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name

class Position(models.Model):
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name
    

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    birthdate = models.DateField(null=True)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE, null=True)
    picture = models.CharField(max_length=500, default="/static/sparky.jpg")
    sex = models.CharField(max_length=1)
    
    def __str__(self):
        return self.user.username

class Assessment(models.Model):
    name = models.CharField(max_length=50)
    units = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Record(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    assessment_result = models.CharField(max_length=50)
    assessment_notes = models.CharField(max_length=500)
    age = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return(f"{self.first_name} {self.last_name}")

class Normative(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    assessment_result = models.CharField(max_length=50)
    age = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return(f"{self.assessment.name} {self.age}")

class Daily(models.Model):
    date = models.DateField()
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    # Recovery
    sleep = models.IntegerField(null=True)
    sleep_score = models.IntegerField(null=True)
    bed_time = models.TimeField(null=True)
    wake_time = models.TimeField(null=True)
    hrv = models.IntegerField(null=True)
    rhr = models.IntegerField(null=True)
    soreness = models.IntegerField(default=False) # Manual
    fatigue = models.IntegerField(default=False) # Manual
    injury = models.IntegerField(default=False) # Manual
    illness = models.IntegerField(default=False) # Manual
    massage = models.BooleanField(default=False) # Manual
    ice = models.BooleanField(default=False) # Manual
    altitude = models.BooleanField(default=False) # Manual
    norma_plus = models.BooleanField(default=False) # Manual
    # Nutrition
    hydration = models.IntegerField(null=True) # Manual
    fruit = models.DecimalField(null=True, max_digits=3, decimal_places=1) # Manual
    vegetable = models.DecimalField(null=True, max_digits=3, decimal_places=1) # Manual
    weight = models.DecimalField(null=True, max_digits=4, decimal_places=1) # Manual
    calories_in = models.IntegerField(null=True)
    calories_out = models.IntegerField(null=True)
    carb = models.IntegerField(null=True)
    sugar = models.IntegerField(null=True)
    fiber = models.IntegerField(null=True)
    protein = models.IntegerField(null=True)
    fat = models.IntegerField(null=True)
    sat_fat = models.IntegerField(null=True)
    unsat_fat = models.IntegerField(null=True)
    omega3 = models.IntegerField(null=True)
    cholesterol = models.IntegerField(null=True)
    sodium = models.IntegerField(null=True)
    potassium = models.IntegerField(null=True)
    calcium = models.IntegerField(null=True)
    iron = models.IntegerField(null=True)
    vitamin_a = models.IntegerField(null=True)
    vitamin_c = models.IntegerField(null=True)
    macro_ratio = models.BooleanField(default=False)
    no_sweets = models.BooleanField(default=False) # Manual
    no_alcohol = models.BooleanField(default=False) # Manual
    beta_alanine = models.BooleanField(default=False) # Manual
    creatine = models.BooleanField(default=False) # Manual
    vitamin_d = models.BooleanField(default=False) # Manual
    # Mental Training
    stress = models.IntegerField(default=False) # Manual
    motivation = models.IntegerField(default=False) # Manual
    read = models.BooleanField(default=False) # Manual
    medidate = models.BooleanField(default=False) # Manual
    visualize = models.BooleanField(default=False) # Manual
    pray = models.BooleanField(default=False) # Manual
    kindness = models.BooleanField(default=False) # Manual
    be_social = models.BooleanField(default=False) # Manual
    # Physical Training
    stretch = models.BooleanField(default=False) # Manual
    mobility = models.BooleanField(default=False) # Manual
    arms = models.BooleanField(default=False) # Manual
    coordination = models.BooleanField(default=False) # Manual
    balance = models.BooleanField(default=False) # Manual
    speed = models.BooleanField(default=False) # Manual
    agility = models.BooleanField(default=False) # Manual
    strength = models.BooleanField(default=False) # Manual
    power = models.BooleanField(default=False) # Manual
    reaction = models.BooleanField(default=False) # Manual
    breathwork = models.BooleanField(default=False) # Manual
    #Notes
    notes = models.CharField(max_length=500) # Manual

    def __str__(self):
        return(f"{self.profile.user.username} {self.date}")
    
class Gear(models.Model):
    name = models.CharField(max_length=50)
    date_purchased = models.DateField()
    mileage = models.IntegerField()
    retired = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
class Workout(models.Model):
    datetime = models.DateTimeField()
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50)
    gear = models.ForeignKey(Gear, on_delete=models.CASCADE)
    # Stats
    total_time = models.IntegerField(null=True)
    distance = models.IntegerField(null=True)
    cadence = models.IntegerField(null=True)
    stride_length = models.DecimalField(max_digits=3, decimal_places=2)
    altitude = models.IntegerField(null=True)
    elevation_gain = models.IntegerField(null=True)
    # Zones
    tiz_hr_recovery = models.IntegerField(null=True)
    tiz_hr_base = models.IntegerField(null=True)
    tiz_hr_tempo = models.IntegerField(null=True)
    tiz_hr_threshold = models.IntegerField(null=True)
    tiz_hr_vo2max = models.IntegerField(null=True)
    tiz_hr_anaerobic = models.IntegerField(null=True)
    tiz_pace_easy = models.IntegerField(null=True)
    tiz_pace_moderate = models.IntegerField(null=True)
    tiz_pace_tempo = models.IntegerField(null=True)
    tiz_pace_threshold = models.IntegerField(null=True)
    tiz_pace_mile = models.IntegerField(null=True)
    tiz_pace_sprint = models.IntegerField(null=True)
    tiz_pwr_recovery = models.IntegerField(null=True)
    tiz_pwr_base = models.IntegerField(null=True)
    tiz_pwr_tempo = models.IntegerField(null=True)
    tiz_pwr_threshold = models.IntegerField(null=True)
    tiz_pwr_vo2max = models.IntegerField(null=True)
    tiz_pwr_anaerobic = models.IntegerField(null=True)
    # Weather
    temp = models.IntegerField(null=True)
    precip = models.CharField(max_length=50, null=True)
    wind = models.IntegerField(null=True)
    wind_dir = models.CharField(max_length=3, null=True)
    dew_point = models.IntegerField(null=True)
    aqi = models.IntegerField(null=True)
    uv = models.IntegerField(null=True)
    # Evaluation
    workout_type = models.CharField(max_length=50, null=True)
    rpe = models.IntegerField(null=True)
    intensity = models.IntegerField(null=True)
    details = models.CharField(max_length=500)
    notes = models.CharField(max_length=500)

    def __str__(self):
        return(f"{self.profile.user.username} {self.date}")