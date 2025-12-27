from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm

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


