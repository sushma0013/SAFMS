from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
@login_required
def dashboard_redirect(request):
    user = request.user

    # If you store role on a Profile model, check that model here.
    # Otherwise, simplest: use is_staff / is_superuser.
    if user.is_superuser or user.is_staff:
        return redirect("admin:index")

    # If your project uses attendance dashboards (confirmed):
    # attendance:student_dashboard and attendance:teacher_dashboard exist.
    # Decide teacher vs student using groups OR a profile role field.

    # Option A: using Django groups "teacher" / "student"
    if user.groups.filter(name="teacher").exists():
        return redirect("attendance:teacher_dashboard")

    return redirect("attendance:student_dashboard")