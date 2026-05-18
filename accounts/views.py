from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def dashboard_redirect(request):
    """After Google login, send user to the right place based on their role."""
    profile = getattr(request.user, "profile", None)

    if request.user.is_superuser:
        return redirect("attendance:admin_dashboard")

    if request.user.groups.filter(name="attendanceadmin").exists():
        return redirect("attendance:admin_dashboard")

    if request.user.groups.filter(name="feesmanager").exists():
        return redirect("attendance:fee_manager_dashboard")

    if profile and profile.role == "teacher":
        return redirect("attendance:teacher_dashboard")

    if profile and profile.role == "student":
        # Student must have a linked StudentProfile to use the system
        from attendance.models import StudentProfile
        try:
            sp = request.user.student_profile
            # Belt-and-braces: ensure linkage actually points back to this user
            if sp.user_id == request.user.id:
                return redirect("attendance:student_dashboard")
        except StudentProfile.DoesNotExist:
            pass
        # No linked StudentProfile yet → make them link
        return redirect("attendance:link_student")

    return redirect("home")


# def google_student(request):
#     request.session["desired_role"] = "student"
#     return redirect("/accounts/google/login/?process=login&next=/dashboard/&prompt=select_account")
from urllib.parse import urlencode

def google_student(request):
    """Start Google OAuth, preserving any ?next= the user was trying to reach."""
    request.session["desired_role"] = "student"

    # If user was redirected here from a protected page (e.g. QR scan),
    # the ?next= will be present. Use it. Otherwise fall back to /dashboard/.
    next_url = request.GET.get("next") or "/dashboard/"

    # Persist next_url across OAuth round-trip via session as a backup
    request.session["post_google_next"] = next_url

    params = urlencode({
        "process": "login",
        "next": next_url,
        "prompt": "select_account",
    })
    return redirect(f"/accounts/google/login/?{params}")

@login_required
def choose_role(request):
    if request.method == "POST":
        role = request.POST.get("role")
        request.user.profile.role = role
        request.user.profile.save()
        return redirect("/dashboard/")
    return render(request, "accounts/choose_role.html")

