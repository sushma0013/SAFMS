# from django.shortcuts import redirect
# from django.contrib.auth.decorators import login_required
# @login_required
# def dashboard_redirect(request):
#     user = request.user

#     # If you store role on a Profile model, check that model here.
#     # Otherwise, simplest: use is_staff / is_superuser.
#     if user.is_superuser or user.is_staff:
#         return redirect("admin:index")

#     # If your project uses attendance dashboards (confirmed):
#     # attendance:student_dashboard and attendance:teacher_dashboard exist.
#     # Decide teacher vs student using groups OR a profile role field.

#     # Option A: using Django groups "teacher" / "student"
#     if user.groups.filter(name="teacher").exists():
#         return redirect("attendance:teacher_dashboard")

#     return redirect("attendance:student_dashboard")

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from accounts.models import Profile
from attendance.models import StudentProfile


# @login_required
# def dashboard_redirect(request):
#     role = getattr(request.user.profile, "role", None)

#     if role == "teacher":
#         return redirect("attendance:teacher_dashboard")
#     if role == "student":
#         return redirect("attendance:student_dashboard")
#     if role == "admin":
#         return redirect("/admin/")

#     # If role not set yet, send to role choose page
#     return redirect("choose_role")


# @login_required
# def dashboard_redirect(request):
#     profile, _ = Profile.objects.get_or_create(user=request.user)
#     role = getattr(profile, "role", None)

#     if request.user.is_superuser or role == "admin":
#         return redirect("admin:index")

#     if role == "teacher":
#         return redirect("attendance:teacher_dashboard")

#     # STUDENT: must be linked to a StudentProfile
#     linked = StudentProfile.objects.filter(user=request.user).exists()
#     if not linked:
#         return redirect("attendance:link_student")

#     return redirect("attendance:student_dashboard")
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required




from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def dashboard_redirect(request):
    profile = getattr(request.user, "profile", None)

    if request.user.is_superuser:
        return redirect("admin:index")

    if profile and profile.role == "teacher":
        return redirect("attendance:teacher_dashboard")

    if profile and profile.role == "student":
        return redirect("attendance:student_dashboard")

    return redirect("home")

# def google_start(request, role):
#     # role will be 'student' or 'teacher' or 'admin'
#     request.session["desired_role"] = role
#     return redirect(f"/accounts/google/login/?process=login&next=/dashboard/")
def google_start(request, role):
    request.session["desired_role"] = role
    return redirect(f"/accounts/google/login/?process=login&next=/dashboard/")


from django.shortcuts import render

@login_required
def choose_role(request):
    if request.method == "POST":
        role = request.POST.get("role")
        request.user.profile.role = role
        request.user.profile.save()
        return redirect("/dashboard/")
    return render(request, "accounts/choose_role.html")

def google_student(request):
    request.session["desired_role"] = "student"
    return redirect("/accounts/google/login/?process=login&next=/dashboard/&prompt=select_account")

