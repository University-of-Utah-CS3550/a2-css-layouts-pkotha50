from . import models
from django.contrib.auth.models import User, Group
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import Assignment
from .models import Submission

# Create your views here.
def index(request):
    assignments = models.Assignment.objects.all()
    return render(request, "index.html", {'assignments': assignments})

def assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)

    total_submissions = assignment.submission_set.count()
    grader = User.objects.get(username='g')
    user_submissions = grader.graded_set.filter(assignment=assignment).count()

    total_students = models.Group.objects.get(name="Students").user_set.count()

    pass_data = {
        "assignment": assignment,
        "total_submissions": total_submissions,
        "user_submissions": user_submissions,
        "total_students": total_students,
    }
    return render(request, "assignment.html", pass_data)

def submissions(request, assignment_id):
    return render(request, "submissions.html")

def profile(request):
    return render(request, "profile.html")

def login_form(request):
    return render(request, "login.html")
