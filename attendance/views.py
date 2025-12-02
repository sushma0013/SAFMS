from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import qrcode
from io import BytesIO
from django.core.files import File
from django.http import HttpResponse
from .models import QRSession

# --- QR Views ---
@login_required
def generate_qr(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        session = QRSession.objects.create(teacher=request.user, subject=subject)
        data = f"Teacher: {request.user.username}, Subject: {subject}, Date: {session.date}"
        qr_img = qrcode.make(data)
        buffer = BytesIO()
        qr_img.save(buffer, 'PNG')
        file_name = f"qr_{session.id}.png"
        session.qr_code.save(file_name, File(buffer), save=True)
        return redirect('show_qr', session_id=session.id)
    return render(request, 'attendance/generate_qr.html')


def show_qr(request, session_id):
    session = QRSession.objects.get(id=session_id)
    return render(request, 'attendance/show_qr.html', {'session': session})


# --- Attendance App Views ---
def attendance_home(request):
    return HttpResponse("<h2>Attendance Home Page</h2>")

def attendance_list(request):
    return HttpResponse("<h2>Attendance List Page</h2>")

def mark_attendance(request, student_id):
    return HttpResponse(f"<h2>Mark Attendance for Student {student_id}</h2>")

# --- Project-level Home View ---
def home(request):
    return HttpResponse("<h2>Smart Attendance System is working!</h2>")
