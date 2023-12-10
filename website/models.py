from django.db import models

class Record(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    sport = models.CharField(max_length=50)
    position = models.CharField(max_length=50)
    assessment = models.CharField(max_length=150)
    assessment_result = models.CharField(max_length=50)
    assessment_units = models.CharField(max_length=50)
    assessment_notes = models.CharField(max_length=500)

    def __str__(self):
        return(f"{self.first_name} {self.last_name}")
