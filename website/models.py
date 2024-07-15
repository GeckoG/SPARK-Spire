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
    
# class Daily(models.Model):
#     date = models.DateField()
#     profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
#     sleep = models.IntegerField()
#     sleep_deep = models.IntegerField()
#     sleep_rem = models.IntegerField()
#     sleep_light = models.IntegerField()
#     sleep_score = models.IntegerField()
#     hrv = models.IntegerField()
#     rhr = models.IntegerField()
#     weight = models.IntegerField()
#     calories_in = models.IntegerField()
#     calories_out = models.IntegerField()
#     hydration = models.IntegerField()
#     stress = models.IntegerField()
#     motivation = models.IntegerField()
#     soreness = models.IntegerField()
#     fatigue = models.IntegerField()
#     stretch = models.BooleanField()
#     roll = models.BooleanField()
#     ice = models.BooleanField()
#     relax = models.BooleanField()
#     read = models.BooleanField()
#     compliment = models.BooleanField()
#     arms = models.BooleanField()
#     balance = models.BooleanField()
#     oxygen = models.BooleanField()
#     focus = models.BooleanField()
#     visualize = models.BooleanField()
#     notes = models.CharField(max_length=500)

#     def __str__(self):
#         return(f"{self.profile.user.username} {self.date}")
    
# class Workout(models.Model):
#     datetime = models.DateTimeField()
#     profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
#     workout_type = models.CharField(max_length=50)
#     intensity_type = models.CharField(max_length=50)
#     total_time = models.IntegerField()
#     tiz_recovery = models.IntegerField()
#     tiz_base = models.IntegerField()
#     tiz_tempo = models.IntegerField()
#     tiz_threshold = models.IntegerField()
#     tiz_vo2max = models.IntegerField()
#     tiz_anaerobic = models.IntegerField()
#     distance = models.IntegerField()
#     cadence = models.IntegerField()
#     stride_length = models.DecimalField(max_digits=3, decimal_places=2)
#     altitude = models.IntegerField()
#     elevation_gain = models.IntegerField()
#     rpe = models.IntegerField()
#     notes = models.CharField(max_length=500)

#     def __str__(self):
#         return(f"{self.profile.user.username} {self.date}")