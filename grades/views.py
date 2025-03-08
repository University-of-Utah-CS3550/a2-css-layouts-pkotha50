from . import models
from django.contrib.auth.models import User, Group
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from decimal import Decimal
from .models import Assignment
from .models import Submission

# Create your views here.
def index(request):
    assignments = models.Assignment.objects.all()
    return render(request, "index.html", {'assignments': assignments})
    
def assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    grader = User.objects.get(username='g')
    alice = User.objects.get(username='a')

    alice_submission = Submission.objects.filter(assignment=assignment, author=alice).first()

    if request.method == "POST" and 'submission_file' in request.FILES:
        submission_file = request.FILES['submission_file']

        if alice_submission:
            alice_submission.file = submission_file
        else:
            alice_submission = Submission.objects.create(
                assignment=assignment,
                author=alice,
                file=submission_file,
                grader=grader,
                score=None
            )

        alice_submission.save()
        return redirect(f"/{assignment_id}/")

    total_submissions = assignment.submission_set.count()
    user_submissions = grader.graded_set.filter(assignment=assignment).count()
    total_students = User.objects.filter(groups__name="Students").count()

    context = {
        "assignment": assignment,
        "total_submissions": total_submissions,
        "user_submissions": user_submissions,
        "total_students": total_students,
        "alice_submission": alice_submission,
    }
    return render(request, "assignment.html", context)

def submissions(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submissions_qs = Submission.objects.filter(assignment=assignment, grader__username='g').order_by('author__username')
    
    errors = {}
    submissions_to_update = []

    if request.method == "POST":
        max_points = assignment.points

        for key, value in request.POST.items():
            if key.startswith('grade-'):
                try:
                    submission_id = int(key.removeprefix('grade-'))
                    submission = Submission.objects.get(id=submission_id, assignment=assignment)

                    if value.strip() == '':
                        submission.score = None
                    else:
                        score = Decimal(value)
                        if score < 0 or score > max_points:
                            raise ValueError("Score must be between 0 and maximum points.")
                        submission.score = score
                    
                    submissions_to_update.append(submission)

                except (ValueError, InvalidOperation):
                    errors.setdefault(submission_id, []).append("Invalid score.")

                except Submission.DoesNotExist:
                    errors.setdefault('invalid_submission', []).append("Invalid submission ID.")

        if submissions_to_update:
            Submission.objects.bulk_update(submissions_to_update, ['score'])

    context = {
        "assignment": assignment,
        "submissions": submissions_qs,
        "errors": errors
    }
    return render(request, "submissions.html", context)

def profile(request):
    grader = User.objects.get(username='g')
    assignments = Assignment.objects.all()
    profile_data = []

    for assignment in assignments:
        total_assigned = grader.graded_set.filter(assignment=assignment).count()
        graded_count = grader.graded_set.filter(assignment=assignment, score__isnull=False).count()
        profile_data.append({
            "assignment": assignment,
            "total_assigned": total_assigned,
            "graded_count": graded_count,
        })

    context = {"profile_data": profile_data}
    return render(request, "profile.html", context)

def login_form(request):
    return render(request, "login.html")

def show_upload(request, filename):
    submission = get_object_or_404(models.Submission, file__name=filename)
    return HttpResponse(submission.file.open())
