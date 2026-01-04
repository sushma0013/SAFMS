from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_redirect(request):
    role = request.user.profile.role  # assuming Profile model has 'role'
    if role == 'teacher':
        return redirect('teacher_dashboard')
    elif role == 'student':
        return redirect('student_dashboard')
    else:
        return redirect('home')

