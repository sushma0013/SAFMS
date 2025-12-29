from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.models import User

def home(request):
      return render(request, 'home.html')
    

def generate_qr(request):
    # your QR generation logic here
    return HttpResponse("QR generated")

def show_qr(request, session_id):
    # your logic to display QR
    return HttpResponse(f"QR for session {session_id}")

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # after registration, go to login page
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})




def login_view(request):
    role = request.GET.get('role')

    if request.method == 'POST':
        username = request.POST['email']   # still coming from email field
        password = request.POST['password']
        role = request.POST['role']

        user = authenticate(request, username=username, password=password)

        if user and user.profile.role == role:
            login(request, user)

            if role == 'teacher':
                return redirect('teacher_dashboard')
            elif role == 'student':
                return redirect('student_dashboard')
            elif role == 'admin':
                return redirect('admin_dashboard')

    return render(request, 'login.html', {'role': role})



def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def teacher_dashboard(request):
    return render(request, 'teacher_dashboard.html')

@login_required
def student_dashboard(request):
    return render(request, 'student_dashboard.html')

@login_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')



def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'User already exists')
            return redirect('signup')

        user = User.objects.create_user(username=username, password=password)
        user.save()

        # assign role
        user.profile.role = role
        user.profile.save()

        return redirect('login')

    return render(request, 'signup.html')






