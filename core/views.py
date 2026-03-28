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
    

# def generate_qr(request):
#     # your QR generation logic here
#     return HttpResponse("QR generated")

# def show_qr(request, session_id):
#     # your logic to display QR
#     return HttpResponse(f"QR for session {session_id}")

# def register(request):
#     if request.method == 'POST':
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('login')  # after registration, go to login page
#     else:
#         form = UserCreationForm()
#     return render(request, 'register.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        print(f"🔍 Login attempt - Username: {username}")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # =========================
# ROLE / GROUP BASED REDIRECT
# =========================

# Super Admin → main admin
            if user.is_superuser:
             return redirect("/admin/")

# Fee Manager → custom fee dashboard
            elif user.groups.filter(name="feesmanager").exists():
             return redirect("attendance:fee_manager_dashboard")

# Teacher
            elif hasattr(user, "profile") and user.profile.role == "teacher":
             return redirect("attendance:teacher_dashboard")

# Student
            elif hasattr(user, "profile") and user.profile.role == "student":
             return redirect("attendance:student_dashboard")

# fallback
            return redirect("home")
            # 🔑 ALWAYS define profile safely
            profile = getattr(user, 'profile', None)
             # 🔁 Handle ?next= redirect (QR FLOW)
            next_url = request.POST.get('next') or request.GET.get('next')

            if next_url:
                return redirect(next_url)

            # 🚨 Superuser/admin
            if user.is_superuser or (profile and profile.role == 'admin'):
                return redirect('admin:index')

            # 👨‍🏫 Teacher
            if profile and profile.role == 'teacher':
                return redirect('attendance:teacher_dashboard')

            # 👨‍🎓 Student
            return redirect('attendance:student_dashboard')

        else:
            print(f"❌ Authentication failed for username: {username}")
            messages.error(request, 'Invalid username or password')

    return render(request, 'login.html')

            
    #         login(request, user)
            
    #         # 🚨 Superuser always goes to admin dashboard
    #         if user.is_superuser:
    #             print(f"→ Redirecting to admin (superuser)")  # DEBUG
    #             return redirect('admin:index')
            
    #         if profile.role == 'admin':
    #             print(f"→ Redirecting to admin dashboard")  # DEBUG
    #             return redirect('admin:index')
    #         elif profile.role == 'teacher':
    #             print(f"→ Redirecting to teacher dashboard")  # DEBUG
    #             return redirect('attendance:teacher_dashboard')
    #         else:
    #             print(f"→ Redirecting to student dashboard")  # DEBUG
    #             return redirect('attendance:student_dashboard')
    #     else:
    #         print(f"❌ Authentication failed for username: {username}")  # DEBUG
        
    #     messages.error(request, 'Invalid username or password')
    
    # return render(request, 'login.html')







def logout_view(request):
    """Logout"""
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('login')


# @login_required
# def teacher_dashboard(request):
#     return render(request, 'teacher_dashboard.html')

# @login_required
# def student_dashboard(request):
#     return render(request, 'student_dashboard.html')

# @login_required
# def admin_dashboard(request):
#     return render(request, 'admin_dashboard.html')




# def signup_view(request):
#     """Signup page"""
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         password2 = request.POST.get('password2')
#         role = request.POST.get('role', 'student')
        
#         # Validation
#         if password != password2:
#             messages.error(request, 'Passwords do not match')
#             return redirect('signup')
        
#         if User.objects.filter(username=username).exists():
#             messages.error(request, 'Username already exists')
#             return redirect('signup')
        
#         try:
#             # Create user with hashed password (IMPORTANT!)
#             user = User.objects.create_user(
#                 username=username, 
#                 password=password  # create_user automatically hashes password
#             )
            
#             # Set role in profile
#             user.profile.role = role
#             user.profile.save()
            
#             messages.success(request, f'Account created successfully as {role}! Please login.')
#             return redirect('login')
#         except Exception as e:
#             messages.error(request, f'Error creating account: {str(e)}')
#             return redirect('signup')
    
#     return render(request, 'signup.html')

from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages

def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role")

        # ✅ Only allow students to self-register
        if role != "student":
            messages.error(request, "Only students can create accounts. Teachers/Admin are created by system administrator.")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("signup")

        user = User.objects.create_user(username=username, password=password)

        # Profile auto-created by signal
        user.profile.role = "student"
        user.profile.save()

        messages.success(request, "Student account created successfully. Please login.")
        return redirect("login")

    return render(request, "signup.html")



