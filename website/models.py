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
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE, null=True)
    
    def __str__(self):
        return self.user.username

class Record(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    assessment = models.CharField(max_length=150)
    assessment_result = models.CharField(max_length=50)
    assessment_units = models.CharField(max_length=50)
    assessment_notes = models.CharField(max_length=500)

    def __str__(self):
        return(f"{self.first_name} {self.last_name}")