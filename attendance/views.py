from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import qrcode
from io import BytesIO
from django.core.files import File
from django.http import HttpResponse
from .models import QRSession, AttendanceRecord,Subject
from django.utils import timezone

# --- QR Views ---
@login_required
def generate_qr(request):
    teacher = request.user
    subjects = Subject.objects.filter(teacher=teacher)

    if not subjects.exists():
        return render(request, 'attendance/no_subject.html', {'teacher': teacher})

    # Pick first subject for today (or add subject selection later)
    subject = subjects.first()

    # Check if today's QR exists and is still valid
    qr_today = QRSession.objects.filter(
        created_by=teacher,
        subject=subject,
        session_date=timezone.now().date(),
        valid_until__gt=timezone.now()
    ).first()

    if qr_today:
        # qr_url = qr_today.qr_code.url
        session = qr_today
    else:
        session = QRSession.objects.create(
            created_by=teacher,
            subject=subject,
            session_date=timezone.now().date()
        )
        # Generate QR using model method
        session.generate_qr(request_domain='http://192.168.1.5:8000')
        # qr_url = session.qr_code.url

    return render(request, 'attendance/generate_qr.html', {
        'qr_url': session.qr_code.url,
        'teacher': teacher,
        'subject': subject,
        'valid_until': session.valid_until
    })






        # Generate QR image
        # data = f"http://192.168.1.5:8000/attendance/mark/{session.uuid}/"  # replace with your local IP
        # qr_img = qrcode.make(data)
        # buffer = BytesIO()
        # qr_img.save(buffer, format='PNG')
        # file_name = f"qr_{session.uuid}.png"
        # session.qr_code.save(file_name, File(buffer), save=True)
        # qr_url = session.qr_code.url

    # return render(request, 'attendance/generate_qr.html', {
    #     'qr_url': qr_url,
    #     'teacher': teacher,
    #     'subject': subject,
    #     'valid_until': session.valid_until
    # })




def show_qr(request, session_id):
    session = QRSession.objects.get(id=session_id)
    return render(request, 'attendance/show_qr.html', {'session': session})




@login_required
def mark_attendance(request, uuid):
    session = get_object_or_404(QRSession, uuid=uuid)

    # Check if QR is still valid
    if session.valid_until < timezone.now():
        return HttpResponse("<h2>This QR code has expired.</h2>")

    # Prevent duplicate attendance
    if not AttendanceRecord.objects.filter(student=request.user, session=session).exists():
        AttendanceRecord.objects.create(
            student=request.user,
            session=session,
            status='Present'
        )

    return HttpResponse("<h2>Attendance marked successfully!</h2>")




# --- Other Views ---
def attendance_home(request):
    return HttpResponse("<h2>Attendance Home Page</h2>")

def attendance_list(request):
    return HttpResponse("<h2>Attendance List Page</h2>")

def home(request):
    return HttpResponse("<h2>Smart Attendance System is working!</h2>")
