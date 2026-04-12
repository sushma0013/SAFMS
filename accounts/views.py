from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


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


def google_student(request):
    request.session["desired_role"] = "student"
    return redirect("/accounts/google/login/?process=login&next=/dashboard/&prompt=select_account")


@login_required
def choose_role(request):
    if request.method == "POST":
        role = request.POST.get("role")
        request.user.profile.role = role
        request.user.profile.save()
        return redirect("/dashboard/")
    return render(request, "accounts/choose_role.html")

