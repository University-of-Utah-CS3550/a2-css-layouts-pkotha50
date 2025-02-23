from django.contrib.auth.models import User, Group
from django.db import models

# Create your models here.
class Assignment(models.Model):
    title = models.CharField(max_length=199)
    description = models.TextField(null=True, blank=True)
    deadline = models.DateTimeField()
    weight = models.IntegerField()
    points = models.IntegerField(default=100)

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    grader = models.ForeignKey(User, related_name='graded_set', null=True, blank=True, on_delete=models.SET_NULL)
    file = models.FileField()
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)