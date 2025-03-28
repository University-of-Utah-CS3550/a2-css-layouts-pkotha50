from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from . import models
from django.contrib.auth.models import User, Group
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.utils.timezone import now
from django.http import HttpResponseBadRequest
from django.db.models import Count
from django.utils.http import url_has_allowed_host_and_scheme
from decimal import Decimal
from .models import Assignment
from .models import Submission

# Create your views here.
@login_required
def index(request):
    assignments = models.Assignment.objects.all()
    return render(request, "index.html", {'assignments': assignments})

@login_required
def assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    user = request.user

    is_student = user.groups.filter(name="Students").exists() or not user.is_authenticated
    is_ta = user.groups.filter(name="TAs").exists()
    is_admin = user.is_superuser

    percentage_score = None
    alice_submission = None
    if is_student and user.is_authenticated:
        alice_submission = Submission.objects.filter(assignment=assignment, author=user).first()

        if alice_submission and alice_submission.score is not None:
            percentage_score = round(float(alice_submission.score) / assignment.points * 100, 2)

        if request.method == "POST" and 'submission_file' in request.FILES:
            if assignment.deadline < now():
                return HttpResponseBadRequest("Assignment deadline has passed.")

            submission_file = request.FILES['submission_file']

            if alice_submission:
                alice_submission.file = submission_file
            else:
                grader = pick_grader(assignment)
                alice_submission = Submission.objects.create(
                    assignment=assignment,
                    author=user,
                    file=submission_file,
                    grader=grader,
                    score=None
                )

            alice_submission.save()
            return redirect(f"/{assignment_id}/")

    total_submissions = assignment.submission_set.count()
    total_students = User.objects.filter(groups__name="Students").count()

    if is_admin:
        user_submissions = total_submissions
    elif is_ta:
        user_submissions = Submission.objects.filter(assignment=assignment, grader=user).count()
    else:
        user_submissions = None

    context = {
        "assignment": assignment,
        "alice_submission": alice_submission,
        "total_submissions": total_submissions,
        "user_submissions": user_submissions,
        "total_students": total_students,
        "is_student": is_student,
        "percentage_score": percentage_score,
    }

    return render(request, "assignment.html", context)

@login_required
def submissions(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    user = request.user

    if not user.groups.filter(name="TAs").exists():
        raise PermissionDenied("Only TAs can access this page.")

    is_admin = user.is_superuser
    is_ta = user.groups.filter(name="TAs").exists()

    if is_admin:
        submissions_qs = Submission.objects.filter(assignment=assignment).order_by('author__username')
    elif is_ta:
        submissions_qs = Submission.objects.filter(assignment=assignment, grader=user).order_by('author__username')
    else:
        return redirect(f"/{assignment_id}/")

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
                        submission.change_grade(user, score)

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
        "errors": errors,
    }
    return render(request, "submissions.html", context)

@login_required
def profile(request):
    user = request.user
    assignments = Assignment.objects.all()

    is_admin = user.is_superuser
    is_ta = user.groups.filter(name="TAs").exists()
    is_student = user.groups.filter(name="Students").exists() or not user.is_authenticated

    if is_admin or is_ta:
        profile_data = []
        for assignment in assignments:
            if is_admin:
                total_assigned = Submission.objects.filter(assignment=assignment).count()
                graded_count = Submission.objects.filter(assignment=assignment, score__isnull=False).count()
            else:
                total_assigned = Submission.objects.filter(assignment=assignment, grader=user).count()
                graded_count = Submission.objects.filter(assignment=assignment, grader=user, score__isnull=False).count()

            profile_data.append({
                "assignment": assignment,
                "total_assigned": total_assigned,
                "graded_count": graded_count,
            })

        context = {
            "is_ta_or_admin": True,
            "profile_data": profile_data,
            "user": user,
        }
        return render(request, "profile.html", context)

    student_data = []
    earned_points = 0
    available_points = 0

    for assignment in assignments:
        submission = Submission.objects.filter(assignment=assignment, author=user).first()
        is_due = assignment.deadline < now()
        points = assignment.points

        if submission:
            if submission.score is not None:
                percent = round(float(submission.score) / points * 100, 2)
                status = f"Your submission received {submission.score}/{points} points ({percent}%)"
                earned_points += percent * (points / 100)
                available_points += points
            elif is_due:
                status = "Your submission is being graded"
            else:
                status = "Your submission is submitted"
        else:
            if is_due:
                status = "Missing, received 0"
                available_points += points
            else:
                status = "Not yet submitted"

        student_data.append({
            "assignment": assignment,
            "status": status,
        })

    current_grade = 100.0 if available_points == 0 else round((earned_points / available_points) * 100, 2)

    context = {
        "is_student": True,
        "student_data": student_data,
        "current_grade": current_grade,
        "user": user,
    }
    return render(request, "profile.html", context)


def login_form(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        next_url = request.POST.get("next", "/profile/")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if url_has_allowed_host_and_scheme(next_url, None):
                return redirect(next_url)
            else:
                return redirect("/")
        else:
            return render(request, "login.html", {
                "error": "Username and password do not match",
                "next": next_url
            })

    next_url = request.GET.get("next", "/profile/")
    return render(request, "login.html", {"next": next_url})

@login_required
def show_upload(request, filename):
    submission = get_object_or_404(models.Submission, file__name=filename)
    return HttpResponse(submission.file.open())

def pick_grader(assignment):
    tas = Group.objects.get(name="TAs").user_set.annotate(
        total_assigned=Count('graded_set', filter=models.Q(graded_set__assignment=assignment))
    ).order_by('total_assigned')
    return tas.first()
