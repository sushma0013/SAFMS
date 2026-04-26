# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.http import HttpResponse
# from django.utils import timezone
# from django.contrib import messages
# from .models import QRSession, AttendanceRecord, Subject
# from datetime import timedelta
# from .utils import close_session_and_mark_absent

# from django.db.models import Count,Q
# from django.contrib.auth.models import User
# from .models import StudentProfile
# from django.contrib.auth.decorators import login_required, user_passes_test
# from .models import StudentProfile, FeeStructure, Payment

# from django.db.models import Sum
# from django.db.models import Sum
# from datetime import timedelta
# from .models import StudentProfile, FeeStructure, Payment, Notification

# import json
# import uuid
# import requests

# from decimal import Decimal
# from django.conf import settings
# from django.urls import reverse
# from django.http import HttpResponseBadRequest



# from .models import Subject, AttendanceRecord, StudentProfile

import json
import uuid
import requests

from decimal import Decimal


from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum, Max
from django.http import HttpResponse, JsonResponse

from django.urls import reverse
from django.utils import timezone

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.db.models import Count, Q
from .models import QRSession, AttendanceRecord, Subject



from .models import AttendanceRecord 



from datetime import timedelta



from .models import StudentProfile, Subject, AttendanceRecord, FeeStructure, Payment, Notification




from .models import Subject, QRSession, AttendanceRecord


from .models import (
    QRSession,
    AttendanceRecord,
    Subject,
    StudentProfile,
    FeeStructure,
    Payment,
    Notification,
    PaymentRequest,
    KhaltiPayment, 
    ClassSchedule,

)

from .utils import close_session_and_mark_absent,get_client_ip,ip_in_allowed_network
from .forms import FeeStructureForm, BulkFeeStructureForm, BulkNotificationForm
from .utils import close_session_and_mark_absent, get_client_ip, ip_in_allowed_network, same_network












NGROK_BASE_URL = "https://sericultural-undefiable-davina.ngrok-free.dev"









# ============= TEACHER VIEWS =============



@login_required
def teacher_dashboard(request):
    if request.user.profile.role != 'teacher':
        messages.error(request, "Teachers only.")
        return redirect('home')

    now = timezone.now()
    today = timezone.localdate()

    # Auto-close expired QR sessions
    expired_sessions = QRSession.objects.filter(
        created_by=request.user,
        is_closed=False,
        valid_until__lte=timezone.now()
    )

    for s in expired_sessions:
        close_session_and_mark_absent(s)

    # Teacher subjects
    subjects = Subject.objects.filter(teacher=request.user)

    # Stats for subject cards/table
    subject_stats = []
    today_present = 0
    today_total = 0

    for subject in subjects:
        total_students = subject.students.count()

        session = QRSession.objects.filter(
            subject=subject,
            session_date=today
        ).order_by('-created_at').first()

        present = AttendanceRecord.objects.filter(
            session=session,
            status='Present'
        ).count() if session else 0

        absent = total_students - present

        today_present += present
        today_total += total_students

        subject_stats.append({
            'subject': subject,
            'total': total_students,
            'present': present,
            'absent': absent,
        })

    attendance_today = round((today_present / today_total) * 100, 2) if today_total else 0

    # Low attendance students
    low_attendance_students = []
    students = AttendanceRecord.objects.filter(
        subject__teacher=request.user
    ).values('student').distinct()

    for s in students:
        student_id = s['student']

        total_classes = AttendanceRecord.objects.filter(
            student_id=student_id,
            subject__teacher=request.user
        ).count()

        present_classes = AttendanceRecord.objects.filter(
            student_id=student_id,
            subject__teacher=request.user,
            status='Present'
        ).count()

        if total_classes > 0:
            percentage = round((present_classes / total_classes) * 100, 2)
            if percentage < 80:
                low_attendance_students.append({
                    'student': User.objects.get(id=student_id),
                    'percentage': percentage
                })

    low_attendance_count = len(low_attendance_students)
    total_students_count = sum(subject.students.count() for subject in subjects)

    # Recent sessions
    recent_sessions = QRSession.objects.filter(
        created_by=request.user
    ).select_related('subject').order_by('-created_at')[:5]

    return render(request, 'attendance/teacher_dashboard.html', {
        'subjects': subjects,
        'subject_stats': subject_stats,
        'attendance_today': attendance_today,
        'low_attendance_students': low_attendance_students,
        'low_attendance_count': low_attendance_count,
        'total_students_count': total_students_count,
        'recent_sessions': recent_sessions,
        'today': today,
        'now': now,
    })







@login_required
def generate_qr(request, subject_id):
    if request.user.profile.role != 'teacher':
        messages.error(request, "Teachers only.")
        return redirect('home')

    subject = get_object_or_404(Subject, id=subject_id, teacher=request.user)

    now = timezone.localtime()
    today = now.date()
    today_name = today.strftime("%A")
    current_time = now.time()

    # Check teacher has this class scheduled right now
    schedule = ClassSchedule.objects.filter(
        subject=subject,
        teacher=request.user,
        day_of_week=today_name,
        is_active=True,
        start_time__lte=current_time,
        end_time__gte=current_time,
    ).first()

    if not schedule:
        messages.error(request, "You can only generate QR during your scheduled class time.")
        return redirect('attendance:teacher_dashboard')

    teacher_ip = get_client_ip(request)
    request_domain = (
        settings.ATTENDANCE_PUBLIC_BASE_URL.rstrip("/")
        if getattr(settings, "ATTENDANCE_PUBLIC_BASE_URL", "")
        else request.build_absolute_uri("/").rstrip("/")
    )

    allowed_network = (schedule.allowed_ip_prefix or "").strip()

    if settings.ATTENDANCE_REQUIRE_ALLOWED_IP_PREFIX and not allowed_network:
        messages.error(
            request,
            "QR generation blocked: set Allowed ip prefix in class schedule (example: 10.24.0.0/19)."
        )
        return redirect("attendance:teacher_dashboard")

    if allowed_network:
        is_loopback = teacher_ip in {"127.0.0.1", "::1"}
        in_allowed_network = ip_in_allowed_network(teacher_ip, allowed_network)
        allow_localhost_bypass = (
            settings.DEBUG
            and settings.ATTENDANCE_ALLOW_LOCALHOST_BYPASS
            and is_loopback
        )

        if settings.ATTENDANCE_STRICT_NETWORK and not in_allowed_network and not allow_localhost_bypass:
            messages.error(
                request,
                f"QR generation blocked: current IP {teacher_ip} is outside allowed network {allowed_network}."
            )
            return redirect("attendance:teacher_dashboard")
     
    active_session = QRSession.objects.filter(
        subject=subject,
        created_by=request.user,
        session_date=today,
        is_closed=False,
        valid_until__gt=now
    ).order_by('-created_at').first()

    if active_session:
        session = active_session
        session.generate_qr(request_domain=request_domain)
        messages.info(request, "Using existing active QR session.")
    else:
        old_open_sessions = QRSession.objects.filter(
            subject=subject,
            created_by=request.user,
            session_date=today,
            is_closed=False,
            valid_until__lte=now
        )
        for s in old_open_sessions:
            close_session_and_mark_absent(s)

        session = QRSession.objects.create(
        subject=subject,
        created_by=request.user,
        session_date=today,
        valid_until=now + timedelta(minutes=15),
        is_closed=False,
        schedule=schedule,
        created_ip=teacher_ip,
        room_name=schedule.room_name,
)
        session.generate_qr(request_domain=request_domain)

        messages.success(request, "New QR generated (valid 15 minutes).")

    qr_url = f"{request_domain}/attendance/mark/{session.uuid}/"
    qr_mode = "NGROK" if "ngrok" in request_domain.lower() else "LAN"

    return render(request, 'attendance/generate_qr.html', {
        'session': session,
        'subject': subject,
        'expires_in': int((session.valid_until - now).total_seconds()),
        'schedule': schedule,
        'teacher_ip': teacher_ip,
        'qr_url': qr_url,
        'qr_mode': qr_mode,
    })

    #     request_domain = f"{request.scheme}://{request.get_host()}"
    #     session.generate_qr(request_domain=request_domain)

    #     messages.success(request, "New QR generated (valid 15 minutes).")
    # qr_url = f"{request.scheme}://{request.get_host()}/attendance/mark/{session.uuid}/"
    # return render(request, 'attendance/generate_qr.html', {
    #     'session': session,
    #     'subject': subject,
    #     'expires_in': int((session.valid_until - now).total_seconds()),
    #     'schedule': schedule,
    #     'teacher_ip': teacher_ip,
    #     'qr_url': qr_url, 
        
    # })



from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

# @login_required
# def student_dashboard(request):
#     if request.user.profile.role != "student":
#         messages.error(request, "Students only.")
#         return redirect("home")

# @login_required
# def student_dashboard(request):
#     print("LOGGED IN USER:", request.user.username)
#     print("ROLE:", getattr(request.user.profile, "role", "NO PROFILE"))

#     if request.user.profile.role != 'student':
#         messages.error(request, "Students only.")
#         return redirect('home')
#     # ✅ get StudentProfile of logged-in student
#     try:
#         profile = request.user.student_profile  # related_name="student_profile"
#     except StudentProfile.DoesNotExist:
#         messages.error(request, "Your student profile is not linked. Contact admin.")
#         return redirect("home")

#     # ==============================
#     # ✅ ATTENDANCE DATA
#     # ==============================
#     enrolled_subjects = Subject.objects.filter(students=request.user)

#     attendance_stats = []
#     total_classes_all = 0
#     total_present_all = 0

#     for subject in enrolled_subjects:
#         total = AttendanceRecord.objects.filter(student=request.user, subject=subject).count()
#         present = AttendanceRecord.objects.filter(student=request.user, subject=subject, status="Present").count()
#         percent = round((present / total) * 100, 2) if total else 0

#         total_classes_all += total
#         total_present_all += present

#         attendance_stats.append({
#             "subject": subject,
#             "total": total,
#             "present": present,
#             "percentage": percent
#         })

#     attendance_records = (
#         AttendanceRecord.objects.filter(student=request.user)
#         .select_related("subject")
#         .order_by("-id")[:10]
#     )

#     # ==============================
#     # ✅ FEE SUMMARY + POPUP NOTIFICATION
#     # ==============================
#     today = timezone.localdate()
#     due_soon_date = today + timedelta(days=7)

#     # defaults (so template never crashes)
#     fee_total = 0.0
#     fee_paid = 0.0
#     fee_remaining = 0.0
#     fee_due_date = None
#     fee_percent = 0
#     popup_notification = None

#     fee = FeeStructure.objects.filter(student=profile).order_by("-semester").first()

#     if fee:
#         fee_total = float(fee.total_fee)
#         fee_due_date = fee.due_date

#         fee_paid = Payment.objects.filter(
#     student=profile,
#     semester=fee.semester,
#     status="COMPLETED"
# ).aggregate(total=Sum("amount"))["total"] or 0

#         # fee_paid = Payment.objects.filter(student=profile, semester=fee.semester).aggregate(
#         #     total=Sum("amount")
#         # )["total"] or 0
#         fee_paid = float(fee_paid)

#         fee_remaining = max(fee_total - fee_paid, 0)
#         fee_percent = int((fee_paid / fee_total) * 100) if fee_total > 0 else 0

#         # ✅ create/update popup reminder only if due soon AND still remaining
#         if fee_due_date and fee_remaining > 0 and today <= fee_due_date <= due_soon_date:
#             title = "Fee Due Reminder"
#             msg = f"Your remaining fee is Rs. {fee_remaining} and due on {fee_due_date}. Please pay before deadline."

#             Notification.objects.update_or_create(
#                 student=profile,
#                 title=title,
#                 is_read=False,
#                 defaults={
#                     "message": msg,
#                     "amount": fee_remaining,
#                     "status": "PENDING",
#                 }
#             )

#             popup_notification = Notification.objects.filter(
#                 student=profile,
#                 is_read=False,
#                 title=title
#             ).order_by("-created_at").first()

#     return render(request, "attendance/student_dashboard.html", {
#         "profile": profile,
#         "enrolled_subjects": enrolled_subjects,
#         "attendance_stats": attendance_stats,
#         "attendance_records": attendance_records,
#         "total_classes_all": total_classes_all,
#         "total_present_all": total_present_all,

#         # ✅ fee values for dashboard cards
#         "fee_total": fee_total,
#         "fee_paid": fee_paid,
#         "fee_remaining": fee_remaining,
#         "fee_due_date": fee_due_date,
#         "fee_percent": fee_percent,

#         # ✅ popup notification
#         "popup_notification": popup_notification,
#     })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404




from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count, Q
from .models import StudentProfile, AttendanceRecord

@login_required
def student_profile(request):
    # Only student can open
    if request.user.profile.role != "student":
        messages.error(request, "Students only.")
        return redirect("home")

    # Get StudentProfile linked to this user
    try:
        profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found. Ask admin to create/link it.")
        return redirect("attendance:student_dashboard")

    # Attendance percent
    total = AttendanceRecord.objects.filter(student=request.user).count()
    present = AttendanceRecord.objects.filter(student=request.user, status="Present").count()
    attendance_percent = round((present / total) * 100, 2) if total else 0

    return render(request, "attendance/student_profile.html", {
        "profile": profile,
        "attendance_percent": attendance_percent,
    })
# @login_required
# def student_profile(request):
#     return render(request, "attendance/student_profile.html")


# @login_required
# def student_dashboard(request):
#     if request.user.profile.role != 'student':
#         messages.error(request, "Students only.")
#         return redirect('home')

#     enrolled_subjects = Subject.objects.filter(students=request.user)

#     attendance_stats = []

#     for subject in enrolled_subjects:
#         total = AttendanceRecord.objects.filter(
#             student=request.user, subject=subject
#         ).count()

#         present = AttendanceRecord.objects.filter(
#             student=request.user, subject=subject, status='Present'
#         ).count()

#         percent = round((present / total) * 100, 2) if total else 0

#         attendance_stats.append({
#             'subject': subject,
#             'total': total,
#             'present': present,
#             'percentage': percent
#         })

#     return render(request, 'attendance/student_dashboard.html', {
#         'enrolled_subjects': enrolled_subjects,
#         'attendance_stats': attendance_stats,
#     })
@login_required
def scan_qr_page(request):
    if request.user.profile.role != 'student':
        messages.error(request, "Students only.")
        return redirect('home')

    return render(request, 'attendance/scan_qr.html')





# @login_required
# def mark_attendance(request, uuid):
#     if request.user.profile.role != 'student':
#         return HttpResponse("Access denied")

#     session = get_object_or_404(QRSession, uuid=uuid)

#     # expired or closed session
#     if session.valid_until < timezone.now() or session.is_closed:
#         if not session.is_closed:
#             close_session_and_mark_absent(session)
#         return render(request, 'attendance/qr_expired.html')

#     # enrolled check
#     if not session.subject.students.filter(id=request.user.id).exists():
#         return HttpResponse("Not enrolled in this subject")

#     # if record exists already
#     record = AttendanceRecord.objects.filter(student=request.user, session=session).first()
#     if record:
#         return render(request, 'attendance/already_marked.html')

#     # mark present
#     AttendanceRecord.objects.create(
#         student=request.user,
#         session=session,
#         subject=session.subject,
#         status='Present'
#     )

#     return render(request, 'attendance/success.html', {'subject': session.subject})

@login_required
def mark_attendance(request, uuid):
    if request.user.profile.role != 'student':
        return HttpResponse("Access denied")

    session = get_object_or_404(QRSession, uuid=uuid)

    if session.valid_until < timezone.now() or session.is_closed:
        if not session.is_closed:
            close_session_and_mark_absent(session)
        return render(request, 'attendance/qr_expired.html')

    if not session.subject.students.filter(id=request.user.id).exists():
        return HttpResponse("Not enrolled in this subject")

    now = timezone.localtime()
    today_name = now.date().strftime("%A")
    current_time = now.time()

    schedule = session.schedule
    if not schedule:
        schedule = ClassSchedule.objects.filter(
            subject=session.subject,
            teacher=session.created_by,
            day_of_week=today_name,
            is_active=True,
            start_time__lte=current_time,
            end_time__gte=current_time,
        ).first()

    if not schedule:
        return HttpResponse("No scheduled class right now for this subject.")

    try:
        student_profile = request.user.student_profile
        if schedule.semester and student_profile.semester and str(student_profile.semester) != str(schedule.semester):
            return HttpResponse("This class is not scheduled for your semester.")
    except StudentProfile.DoesNotExist:
        return HttpResponse("Student profile not found.")
    student_ip = get_client_ip(request)
    allowed_network = (schedule.allowed_ip_prefix or "").strip()

    if settings.ATTENDANCE_REQUIRE_ALLOWED_IP_PREFIX and not allowed_network:
        messages.error(
            request,
            "Attendance blocked: class schedule has no Allowed ip prefix configured."
        )
        return redirect("attendance:student_dashboard")

    print("=" * 50)
    print("STUDENT IP:", student_ip)
    print("ALLOWED NETWORK:", allowed_network or "<none>")
    print("=" * 50)

    if settings.ATTENDANCE_STRICT_NETWORK and allowed_network and not ip_in_allowed_network(student_ip, allowed_network):
        messages.error(
            request,
            f"Attendance can only be marked from allowed network ({allowed_network})."
        )
        return redirect("attendance:student_dashboard")
    # student_ip = get_client_ip(request)

    # print("TEACHER IP:", session.created_ip)
    # print("STUDENT IP:", student_ip)

    # if not same_network(student_ip, session.created_ip):
    #    messages.error(
    #     request,
    #     "Attendance can only be marked from same campus network."
    # )
    # return redirect("attendance:student_dashboard") 

    record = AttendanceRecord.objects.filter(student=request.user, session=session).first()
    if record:
        return render(request, 'attendance/already_marked.html')

    AttendanceRecord.objects.create(
        student=request.user,
        session=session,
        subject=session.subject,
        status='Present'
    )

    return render(request, 'attendance/success.html', {
        'subject': session.subject,
        'schedule': schedule,
        'student_ip': student_ip,
    })

@login_required
def teacher_profile(request):
    teacher = request.user
    subjects = Subject.objects.filter(teacher=teacher)

    total_students = sum(s.students.count() for s in subjects)

    return render(request, 'attendance/teacher_profile.html', {
        'teacher': teacher,
        'subjects': subjects,
        'total_students': total_students
    })
from django.db.models import Count, Q, Max
from django.utils import timezone

@login_required
def teacher_students(request):
    if request.user.profile.role != 'teacher':
        return redirect('home')

    subjects = Subject.objects.filter(teacher=request.user)
    students = User.objects.filter(enrolled_subjects__in=subjects).distinct()

    today = timezone.now().date()

    # --- Top cards ---
    total_students = students.count()

    present_today_count = AttendanceRecord.objects.filter(
        subject__in=subjects,
        date=today,
        status='Present'
    ).values('student').distinct().count()

    absent_today_count = total_students - present_today_count

    # --- Per-student attendance stats ---
    # totals + present counts per student
    stats = AttendanceRecord.objects.filter(
        subject__in=subjects,
        student__in=students
    ).values('student').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='Present')),
        last_time=Max('recorded_at'),
    )

    stats_map = {row['student']: row for row in stats}

    # last status per student (based on latest recorded_at)
    # (simple method: query once per student for last record; OK for small class sizes)
    student_rows = []
    low_attendance_ids = set()

    for st in students:
        row = stats_map.get(st.id, {'total': 0, 'present': 0})

        total = row.get('total', 0)
        present = row.get('present', 0)
        percent = round((present / total) * 100, 2) if total else 0

        last_record = AttendanceRecord.objects.filter(
            student=st,
            subject__in=subjects
        ).order_by('-recorded_at').select_related('subject').first()

        last_status = last_record.status if last_record else "No Record"

        if total > 0 and percent < 80:
            low_attendance_ids.add(st.id)

        student_rows.append({
            "student": st,
            "percent": percent,
            "last_status": last_status,
        })

    low_attendance_count = len(low_attendance_ids)

    return render(request, "attendance/teacher_students.html", {
        "students_data": student_rows,           # ✅ use this in template
        "total_students": total_students,
        "present_today_count": present_today_count,
        "absent_today_count": absent_today_count,
        "low_attendance_count": low_attendance_count,
        "low_attendance_ids": low_attendance_ids,
    })




# @login_required
# def teacher_students(request):
#     if request.user.profile.role != 'teacher':
#         messages.error(request, "Teachers only.")
#         return redirect('home')

#     today = timezone.localdate()
#     subjects = Subject.objects.filter(teacher=request.user)

#     # ✅ Correct: uses related_name='enrolled_subjects'
#     students = User.objects.filter(enrolled_subjects__in=subjects).distinct()

#     today_present = AttendanceRecord.objects.filter(
#         subject__in=subjects,
#         date=today,
#         status='Present'
#     ).select_related('student', 'subject')

#     today_absent = AttendanceRecord.objects.filter(
#         subject__in=subjects,
#         date=today,
#         status='Absent'
#     ).select_related('student', 'subject')

#     low_attendance_students = []
#     for student in students:
#         total = AttendanceRecord.objects.filter(student=student, subject__in=subjects).count()
#         present = AttendanceRecord.objects.filter(student=student, subject__in=subjects, status='Present').count()
#         if total > 0:
#             percent = (present / total) * 100
#             if percent < 80:
#                 low_attendance_students.append({
#                     'student': student,
#                     'percentage': round(percent, 2)
#                 })

#     return render(request, 'attendance/teacher_students.html', {
#         'total_students': students.count(),
#         'present_today_count': today_present.count(),
#         'absent_today_count': today_absent.count(),
#         'low_attendance_count': len(low_attendance_students),

#         'today_present': today_present,
#         'today_absent': today_absent,
#         'low_attendance_students': low_attendance_students,
#         'today': today,
#     })


# @login_required
# def teacher_students(request):
#     if request.user.profile.role != 'teacher':
#         messages.error(request, "Teachers only.")
#         return redirect('home')

#     today = timezone.now().date()

#     subjects = Subject.objects.filter(teacher=request.user)

#     # All students taught by this teacher
#     students = User.objects.filter(
#         attendancerecord__subject__in=subjects
#     ).distinct()

#     # TODAY PRESENT
#     today_present = AttendanceRecord.objects.filter(
#         subject__in=subjects,
#         date=today,
#         status='Present'
#     ).select_related('student', 'subject')

#     # TODAY ABSENT
#     today_absent = AttendanceRecord.objects.filter(
#         subject__in=subjects,
#         date=today,
#         status='Absent'
#     ).select_related('student', 'subject')

#     # LOW ATTENDANCE (<80%)
#     low_attendance_students = []

#     for student in students:
#         total = AttendanceRecord.objects.filter(
#             student=student,
#             subject__in=subjects
#         ).count()

#         present = AttendanceRecord.objects.filter(
#             student=student,
#             subject__in=subjects,
#             status='Present'
#         ).count()

#         percent = (present / total) * 100 if total else 0

#         if percent < 80:
#             low_attendance_students.append({
#                 'student': student,
#                 'percentage': round(percent, 2)
#             })

#     return render(request, 'attendance/teacher_students.html', {
#         'today_present': today_present,
#         'today_absent': today_absent,
#         'low_attendance_students': low_attendance_students
#     })




@login_required
def my_classes(request):
    if request.user.profile.role != 'teacher':
        messages.error(request, "Teachers only.")
        return redirect('home')

    expired_sessions = QRSession.objects.filter(
        created_by=request.user,
        is_closed=False,
        valid_until__lte=timezone.now()
    )

    for s in expired_sessions:
        close_session_and_mark_absent(s)

    today = timezone.localdate()

    sessions_today = (
        QRSession.objects
        .filter(created_by=request.user, session_date=today)
        .select_related("subject")
        .annotate(
            present_count=Count(
                "attendance_records",
                filter=Q(attendance_records__status="Present")
            ),
            absent_count=Count(
                "attendance_records",
                filter=Q(attendance_records__status="Absent")
            ),
            total_marked=Count("attendance_records"),
        )
        .order_by("-created_at")
    )

    all_sessions = (
        QRSession.objects
        .filter(created_by=request.user)
        .select_related("subject", "schedule")
        .annotate(
            present_count=Count(
                "attendance_records",
                filter=Q(attendance_records__status="Present")
            ),
            absent_count=Count(
                "attendance_records",
                filter=Q(attendance_records__status="Absent")
            ),
            total_marked=Count("attendance_records"),
        )
        .order_by("-created_at")
    )

    total_present_all = sum(s.present_count for s in sessions_today)
    total_absent_all = sum(s.absent_count for s in sessions_today)

    teacher_schedule = ClassSchedule.objects.filter(
        teacher=request.user,
        is_active=True
    ).order_by("day_of_week", "start_time")

    now_local = timezone.localtime()
    today_name = now_local.strftime("%A")
    current_time = now_local.time()

    for sch in teacher_schedule:
      if not sch.is_active:
        sch.display_status = "Inactive"
        sch.status_color = "gray"
      elif sch.day_of_week == today_name:
        if sch.start_time <= current_time <= sch.end_time:
            sch.display_status = "Live Now"
            sch.status_color = "green"
        elif current_time < sch.start_time:
            sch.display_status = "Upcoming Today"
            sch.status_color = "blue"
        else:
            sch.display_status = "Finished Today"
            sch.status_color = "gray"
    else:
        sch.display_status = "Scheduled"
        sch.status_color = "indigo"

    return render(request, "attendance/my_classes.html", {
        "sessions_today": sessions_today,
        "all_sessions": all_sessions,
        "today": today,
        "total_present_all": total_present_all,
        "total_absent_all": total_absent_all,
        "teacher_schedule": teacher_schedule,
    })

@login_required
def class_session_detail(request, session_id):
    if request.user.profile.role != 'teacher':
        messages.error(request, "Teachers only.")
        return redirect('home')

    session = get_object_or_404(
        QRSession.objects.select_related("subject"),
        id=session_id,
        created_by=request.user
    )

    present_records = AttendanceRecord.objects.filter(
        session=session, status="Present"
    ).select_related("student")

    absent_records = AttendanceRecord.objects.filter(
        session=session, status="Absent"
    ).select_related("student")

    return render(request, "attendance/class_session_detail.html", {
        "session": session,
        "present_records": present_records,
        "absent_records": absent_records,
    })







@login_required
def link_student(request):
    if request.method == "POST":
        student_id = request.POST.get("student_id")

        try:
            student = StudentProfile.objects.get(student_id=student_id)

            # link Google user to student
            student.user = request.user
            student.save()
            return redirect("accounts:dashboard")

            # return redirect("attendance:student_dashboard")

        except StudentProfile.DoesNotExist:
            return render(
                request,
                "attendance/link_student.html",
                {"error": "Invalid Student ID"}
            )

    return render(request, "attendance/link_student.html")


@login_required
def teacher_reports(request):
    # only teacher can open
    if request.user.profile.role != "teacher":
        messages.error(request, "Teachers only.")
        return redirect("home")

    today = timezone.localdate()

    # all subjects taught by this teacher
    subjects = Subject.objects.filter(teacher=request.user)

    # all students under this teacher
    students = User.objects.filter(enrolled_subjects__in=subjects).distinct()

    # -----------------------------
    # top summary counts
    # -----------------------------
    total_students = students.count()

    present_today_count = AttendanceRecord.objects.filter(
        subject__in=subjects,
        date=today,
        status="Present"
    ).values("student").distinct().count()

    absent_today_count = total_students - present_today_count

    # -----------------------------
    # build student report rows
    # -----------------------------
    report_rows = []
    low_attendance_count = 0

    for student in students:
        total_classes = AttendanceRecord.objects.filter(
            student=student,
            subject__in=subjects
        ).count()

        present_classes = AttendanceRecord.objects.filter(
            student=student,
            subject__in=subjects,
            status="Present"
        ).count()

        absent_classes = AttendanceRecord.objects.filter(
            student=student,
            subject__in=subjects,
            status="Absent"
        ).count()

        attendance_percent = round((present_classes / total_classes) * 100, 2) if total_classes else 0

        # latest attendance record
        last_record = AttendanceRecord.objects.filter(
            student=student,
            subject__in=subjects
        ).order_by("-recorded_at").first()

        last_status = last_record.status if last_record else "No Record"
        last_subject = last_record.subject.code if last_record else "-"
        last_date = last_record.date if last_record else None

        # student full name from StudentProfile if exists
        try:
            student_name = student.student_profile.full_name
            student_id = student.student_profile.student_id
        except:
            student_name = student.username
            student_id = student.id

        # risk check
        is_risk = total_classes > 0 and attendance_percent < 80
        if is_risk:
            low_attendance_count += 1

        report_rows.append({
            "student_name": student_name,
            "student_id": student_id,
            "total_classes": total_classes,
            "present_classes": present_classes,
            "absent_classes": absent_classes,
            "attendance_percent": attendance_percent,
            "last_status": last_status,
            "last_subject": last_subject,
            "last_date": last_date,
            "is_risk": is_risk,
        })

    context = {
        "today": today,
        "teacher": request.user,
        "subjects": subjects,
        "total_students": total_students,
        "present_today_count": present_today_count,
        "absent_today_count": absent_today_count,
        "low_attendance_count": low_attendance_count,
        "report_rows": report_rows,
    }

    return render(request, "attendance/teacher_reports.html", context)

@login_required
def teacher_settings(request):
    return render(request, "attendance/teacher_settings.html")




@login_required
def teacher_add_student(request):
    if request.user.profile.role != "teacher":
        messages.error(request, "Teachers only.")
        return redirect("home")

    subjects = Subject.objects.filter(teacher=request.user)

    if request.method == "POST":
        username = request.POST.get("username")
        subject_id = request.POST.get("subject_id")

        student = User.objects.filter(username=username).first()
        subject = Subject.objects.filter(id=subject_id, teacher=request.user).first()

        if not student:
            messages.error(request, "Student username not found.")
            return redirect("attendance:teacher_add_student")

        if not subject:
            messages.error(request, "Invalid subject.")
            return redirect("attendance:teacher_add_student")
        subject.students.add(student)

    StudentProfile.objects.get_or_create(
    user=student,
    defaults={
        "student_id": f"STD-{student.id}",
        "full_name": student.get_full_name() or student.username,
    }
)

    messages.success(request, f"{student.username} enrolled in {subject.code} and added to student records.")
    return redirect("attendance:teacher_students")


   


@login_required
def my_attendance(request):
    if request.user.profile.role != "student":
        messages.error(request, "Students only.")
        return redirect("home")

    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not linked.")
        return redirect("attendance:student_dashboard")

    enrolled_subjects = Subject.objects.filter(students=request.user)

    subject_stats = []
    total_classes = 0
    total_present = 0

    for subject in enrolled_subjects:
        total = AttendanceRecord.objects.filter(student=request.user, subject=subject).count()
        present = AttendanceRecord.objects.filter(student=request.user, subject=subject, status="Present").count()
        absent = AttendanceRecord.objects.filter(student=request.user, subject=subject, status="Absent").count()
        percentage = round((present / total) * 100, 2) if total else 0

        total_classes += total
        total_present += present

        subject_stats.append({
            "subject": subject,
            "total": total,
            "present": present,
            "absent": absent,
            "percentage": percentage,
        })

    total_absent = total_classes - total_present
    overall_percentage = round((total_present / total_classes) * 100, 2) if total_classes else 0

    recent_records = AttendanceRecord.objects.filter(
        student=request.user
    ).select_related("subject").order_by("-date", "-recorded_at")[:10]

    context = {
        "profile": profile,
        "subject_stats": subject_stats,
        "total_classes": total_classes,
        "total_present": total_present,
        "total_absent": total_absent,
        "overall_percentage": overall_percentage,
        "recent_records": recent_records,
    }
    return render(request, "attendance/my_attendance.html", context)



from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import StudentProfile, FeeStructure, Payment


@login_required
def my_fees(request):
    # ✅ only student can open
    if request.user.profile.role != "student":
        messages.error(request, "Students only.")
        return redirect("home")

    # ✅ get linked StudentProfile (related_name="student_profile")
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Your student profile is not linked. Contact admin.")
        return redirect("attendance:student_dashboard")

    # ✅ optional semester filter: /attendance/student/my-fees/?semester=2
    semester_qs = request.GET.get("semester")
    semester = int(semester_qs) if semester_qs and semester_qs.isdigit() else None

    # ✅ get fee structure (latest or selected semester)
    fee_qs = FeeStructure.objects.filter(student=profile)
    if semester is not None:
        fee_qs = fee_qs.filter(semester=semester)

    fee = fee_qs.order_by("-semester").first()

    # ✅ decide which semester to show
    current_semester = fee.semester if fee else (semester or 1)

    # ✅ payments only for this semester
    payments = Payment.objects.filter(
    student=profile,
    semester=current_semester,
    status="COMPLETED"
).order_by("-paid_at")

    paid_amount = payments.aggregate(total=Sum("amount"))["total"] or 0

    # ✅ totals (keep Decimal, don’t convert to float)
    total_fee = fee.total_fee if fee else 0
    remaining = total_fee - paid_amount if fee else 0
    due_date = fee.due_date if fee else None

    context = {
        "profile": profile,
        "fee": fee,
        "semester": current_semester,
        "total_fee": total_fee,
        "paid_amount": paid_amount,
        "remaining": remaining,
        "due_date": due_date,
        "payments": payments,
    }
    return render(request, "attendance/my_fees.html", context)


def fee_manager_only(user):
    return user.is_authenticated and user.groups.filter(name="feesmanager").exists()
@login_required
@user_passes_test(fee_manager_only)
def bulk_fee_structure(request):
    if request.method == "POST":
        form = BulkFeeStructureForm(request.POST)
        if form.is_valid():
            students = form.cleaned_data["students"]
            semester = form.cleaned_data["semester"]
            total_fee = form.cleaned_data["total_fee"]
            due_date = form.cleaned_data["due_date"]
            only_without_fee = form.cleaned_data["only_without_fee"]
            overwrite_existing = form.cleaned_data["overwrite_existing"]

            if only_without_fee:
                students = StudentProfile.objects.exclude(
                    id__in=FeeStructure.objects.filter(
                        semester=semester
                    ).values_list("student_id", flat=True)
                ).order_by("full_name")

            count = 0

            for student in students:
                existing = FeeStructure.objects.filter(
                    student=student,
                    semester=semester
                ).first()

                if existing:
                    if overwrite_existing:
                        existing.total_fee = total_fee
                        existing.due_date = due_date
                        existing.save()
                        count += 1
                else:
                    FeeStructure.objects.create(
                        student=student,
                        semester=semester,
                        total_fee=total_fee,
                        due_date=due_date
                    )
                    count += 1

            messages.success(request, f"{count} fee structure(s) processed successfully.")
            return redirect("attendance:fee_structures_page")
    else:
        form = BulkFeeStructureForm()

    return render(request, "attendance/bulk_fee_structure.html", {
        "form": form
    })

@login_required
@user_passes_test(fee_manager_only)
def notifications_page(request):
    query = request.GET.get("q", "")
    unread = request.GET.get("unread", "")

    notifications = Notification.objects.select_related("student").order_by("-created_at")

    if query:
        notifications = notifications.filter(
            Q(student__full_name__icontains=query) |
            Q(student__student_id__icontains=query) |
            Q(title__icontains=query)
        )

    if unread == "yes":
        notifications = notifications.filter(is_read=False)
    elif unread == "no":
        notifications = notifications.filter(is_read=True)

    context = {
        "notifications": notifications,
        "query": query,
        "selected_unread": unread,
        "total_count": notifications.count(),
    }
    return render(request, "attendance/notifications_page.html", context)


@login_required
@user_passes_test(fee_manager_only)
def bulk_notification(request):
    if request.method == "POST":
        form = BulkNotificationForm(request.POST)
        if form.is_valid():
            students = form.cleaned_data["students"]
            title = form.cleaned_data["title"]
            message = form.cleaned_data["message"]
            amount = form.cleaned_data["amount"]
            only_students_with_fee = form.cleaned_data["only_students_with_fee"]

            if only_students_with_fee:
                students = StudentProfile.objects.filter(
                    id__in=FeeStructure.objects.values_list("student_id", flat=True)
                ).distinct().order_by("full_name")

            count = 0

            for student in students:
                Notification.objects.create(
                    student=student,
                    title=title,
                    message=message,
                    amount=amount,
                    status="PENDING",
                    is_read=False
                )
                count += 1

            messages.success(request, f"{count} notification(s) sent successfully.")
            return redirect("attendance:fee_manager_dashboard")
    else:
        form = BulkNotificationForm()

    return render(request, "attendance/bulk_notification.html", {
        "form": form
    })


from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.utils import timezone

from .models import StudentProfile, Subject, AttendanceRecord, FeeStructure, Payment


@login_required
def student_report(request):
    if request.user.profile.role != "student":
        messages.error(request, "Students only.")
        return redirect("home")

    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not linked.")
        return redirect("attendance:student_dashboard")

    # -----------------------------
    # Attendance summary
    # -----------------------------
    enrolled_subjects = Subject.objects.filter(students=request.user)

    subject_stats = []
    total_classes = 0
    total_present = 0

    for subject in enrolled_subjects:
        total = AttendanceRecord.objects.filter(student=request.user, subject=subject).count()
        present = AttendanceRecord.objects.filter(student=request.user, subject=subject, status="Present").count()
        absent = AttendanceRecord.objects.filter(student=request.user, subject=subject, status="Absent").count()
        percentage = round((present / total) * 100, 2) if total else 0

        total_classes += total
        total_present += present

        subject_stats.append({
            "subject": subject,
            "total": total,
            "present": present,
            "absent": absent,
            "percentage": percentage,
        })

    total_absent = total_classes - total_present
    overall_percentage = round((total_present / total_classes) * 100, 2) if total_classes else 0

    if overall_percentage >= 75:
        attendance_status = "Good"
        attendance_status_color = "text-green-600"
        attendance_message = f"Your current attendance is {overall_percentage}%, which is above the 75% threshold."
        exam_eligible = True
    else:
        attendance_status = "Warning"
        attendance_status_color = "text-orange-600"
        attendance_message = f"Your current attendance is {overall_percentage}%, which is below the 75% threshold."
        exam_eligible = False

    # -----------------------------
    # Fee summary
    # -----------------------------
    fee = FeeStructure.objects.filter(student=profile).order_by("-semester").first()

    total_fee = fee.total_fee if fee else 0
    due_date = fee.due_date if fee else None
    current_semester = fee.semester if fee else 1

    payments = Payment.objects.filter(
    student=profile,
    semester=current_semester,
    status="COMPLETED"
).order_by("-paid_at")
    paid_amount = payments.aggregate(total=Sum("amount"))["total"] or 0
    remaining_due = total_fee - paid_amount if fee else 0

    if fee:
        if remaining_due <= 0:
            fee_status = "Paid"
            fee_status_color = "text-green-600"
            fee_clearance = True
        elif paid_amount > 0:
            fee_status = "Partial"
            fee_status_color = "text-orange-500"
            fee_clearance = False
        else:
            fee_status = "Due"
            fee_status_color = "text-red-600"
            fee_clearance = False
    else:
        fee_status = "Not Set"
        fee_status_color = "text-slate-500"
        fee_clearance = False

    report_date = timezone.localdate()

    context = {
        "profile": profile,
        "report_date": report_date,

        # attendance
        "subject_stats": subject_stats,
        "total_classes": total_classes,
        "total_present": total_present,
        "total_absent": total_absent,
        "overall_percentage": overall_percentage,
        "attendance_status": attendance_status,
        "attendance_status_color": attendance_status_color,
        "attendance_message": attendance_message,
        "exam_eligible": exam_eligible,

        # fees
        "total_fee": total_fee,
        "paid_amount": paid_amount,
        "remaining_due": remaining_due,
        "due_date": due_date,
        "fee_status": fee_status,
        "fee_status_color": fee_status_color,
        "fee_clearance": fee_clearance,
        "payments": payments,
        "current_semester": current_semester,
    }

    return render(request, "attendance/student_report.html", context)


@login_required
def student_settings(request):
    if request.user.profile.role != 'student':
        messages.error(request, "Students only.")
        return redirect('home')
    return render(request, "attendance/student_settings.html")


from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta


from .models import StudentProfile, FeeStructure, Payment

# def fee_manager_only(user):
#     return (
#         user.is_authenticated and
#         user.is_staff and
#         user.groups.filter(name="feesmanager").exists()
#     )

@login_required
@user_passes_test(fee_manager_only)
def fee_manager_dashboard(request):

    total_students = StudentProfile.objects.count()
    total_fee_set = FeeStructure.objects.count()

    # Only completed payments counted
    total_collected = Payment.objects.filter(
        status="COMPLETED"
    ).aggregate(total=Sum("amount"))["total"] or 0

    fee_rows = FeeStructure.objects.select_related("student").all()

    due_students = 0
    due_soon_students = 0

    today = timezone.localdate()
    due_soon_date = today + timedelta(days=7)

    for fee in fee_rows:
        paid = Payment.objects.filter(
            student=fee.student,
            semester=fee.semester,
            status="COMPLETED"
        ).aggregate(total=Sum("amount"))["total"] or 0

        remaining = fee.total_fee - paid

        if remaining > 0:
            due_students += 1

            if fee.due_date and today <= fee.due_date <= due_soon_date:
                due_soon_students += 1

    # Only completed payments
    recent_payments = Payment.objects.filter(
        status="COMPLETED"
    ).select_related("student").order_by("-paid_at")[:8]

    context = {
        "total_students": total_students,
        "total_fee_set": total_fee_set,
        "total_collected": total_collected,
        "due_students": due_students,
        "due_soon_students": due_soon_students,
        "recent_payments": recent_payments,
    }

    return render(request, "attendance/fee_manager_dashboard.html", context)

from django.db.models import Sum
from django.utils import timezone
from .models import PaymentRequest, Payment, Notification

# @login_required
# def create_payment_request(request):

#     if request.user.profile.role != "student":
#         messages.error(request, "Students only.")
#         return redirect("home")

#     student = get_object_or_404(StudentProfile, user=request.user)

#     if request.method == "POST":
#         semester = int(request.POST.get("semester", 1))
#         amount = request.POST.get("amount")
#         note = request.POST.get("note", "")
#         proof = request.FILES.get("proof")

#         PaymentRequest.objects.create(
#             student=student,
#             semester=semester,
#             amount=amount,
#             note=note,
#             proof=proof,
#             status="PENDING",
#         )

#         messages.success(request, "Payment request submitted. Waiting for approval.")
#         return redirect("attendance:my_fees")

#     return render(request, "attendance/payment_request_form.html")




# @login_required
# @user_passes_test(fee_manager_only)
# def fee_manager_requests(request):
#     requests = PaymentRequest.objects.select_related("student").order_by("-created_at")
#     return render(request, "attendance/fee_manager_requests.html", {"requests": requests})

# @login_required
# @user_passes_test(fee_manager_only)
# def approve_payment_request(request, pk):

#     pr = get_object_or_404(PaymentRequest, pk=pk)

#     if pr.status != "PENDING":
#         messages.info(request, "Already reviewed.")
#         return redirect("attendance:fee_manager_requests")

#     # Create final Payment record
#     Payment.objects.create(
#         student=pr.student,
#         semester=pr.semester,
#         amount=pr.amount,
#         note=f"Approved: {pr.note}",
#         payment_method="MANUAL",   # manual payment
#         status="COMPLETED",        # approved = completed
#     )

#     pr.status = "APPROVED"
#     pr.reviewed_by = request.user
#     pr.reviewed_at = timezone.now()
#     pr.save()

#     Notification.objects.create(
#         student=pr.student,
#         title="Payment Approved",
#         message=f"Your payment of Rs {pr.amount} has been approved.",
#         amount=pr.amount,
#         status="SENT",
#     )

#     messages.success(request, "Approved and added to Payments.")
#     return redirect("attendance:fee_manager_requests")

# @login_required
# @user_passes_test(fee_manager_only)
# def reject_payment_request(request, pk):

#     pr = get_object_or_404(PaymentRequest, pk=pk)

#     if pr.status != "PENDING":
#         messages.info(request, "Already reviewed.")
#         return redirect("attendance:fee_manager_requests")

#     pr.status = "REJECTED"
#     pr.reviewed_by = request.user
#     pr.reviewed_at = timezone.now()
#     pr.save()

#     Notification.objects.create(
#         student=pr.student,
#         title="Payment Rejected",
#         message="Your payment proof was rejected. Please submit again with correct details.",
#         status="SENT",
#     )

#     messages.error(request, "Payment request rejected.")
#     return redirect("attendance:fee_manager_requests")



from django.http import JsonResponse

@login_required
def mark_notification_read(request, notif_id):
    try:
        profile = request.user.student_profile
        n = Notification.objects.get(id=notif_id, student=profile)

        n.is_read = True
        n.status = "READ"
        n.save()

        return JsonResponse({"ok": True})
    except:
        return JsonResponse({"ok": False}, status=400)
    
@login_required
def khalti_initiate_payment(request):
    if request.user.profile.role != "student":
        messages.error(request, "Students only.")
        return redirect("home")

    student = get_object_or_404(StudentProfile, user=request.user)

    fee = FeeStructure.objects.filter(student=student).order_by("-semester").first()
    if not fee:
        messages.error(request, "Fee structure not found.")
        return redirect("attendance:my_fees")

    semester = fee.semester

    paid_amount = Payment.objects.filter(
        student=student,
        semester=semester,
        status="COMPLETED"
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    remaining = fee.total_fee - paid_amount

    if remaining <= 0:
        messages.success(request, "No remaining amount to pay.")
        return redirect("attendance:my_fees")

    purchase_order_id = f"FEE-{student.id}-{semester}-{uuid.uuid4().hex[:8]}"
    return_url = request.build_absolute_uri(reverse("attendance:khalti_verify"))

    payload = {
        "return_url": return_url,
        "website_url": settings.KHALTI_WEBSITE_URL,
        "amount": int(remaining * 100),  # paisa
        "purchase_order_id": purchase_order_id,
        "purchase_order_name": f"Semester {semester} Fee Payment",
    }

    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://dev.khalti.com/api/v2/epayment/initiate/",
        headers=headers,
        json=payload,
        timeout=20,
    )

    print("KHALTI INITIATE STATUS:", response.status_code)
    print("KHALTI INITIATE BODY:", response.text)
    print("RETURN URL:", return_url)
    print("WEBSITE URL:", settings.KHALTI_WEBSITE_URL)

    if response.status_code != 200:
        messages.error(request, f"Khalti initiate failed: {response.text}")
        return redirect("attendance:my_fees")

    data = response.json()
    payment_url = data.get("payment_url")
    pidx = data.get("pidx")

    if not payment_url or not pidx:
        messages.error(request, f"Khalti did not return payment_url/pidx: {data}")
        return redirect("attendance:my_fees")

    KhaltiPayment.objects.create(
        student=student,
        semester=semester,
        amount=remaining,
        purchase_order_id=purchase_order_id,
        purchase_order_name=payload["purchase_order_name"],
        pidx=pidx,
        status="INITIATED",
    )

    return redirect(payment_url)

@login_required
def khalti_verify_payment(request):
    # Khalti sends pidx back after payment
    pidx = request.GET.get("pidx")
    if not pidx:
        messages.error(request, "Missing Khalti payment identifier.")
        return redirect("attendance:my_fees")

    khalti_payment = get_object_or_404(KhaltiPayment, pidx=pidx)

    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    payload = {"pidx": pidx}

    response = requests.post(
        "https://dev.khalti.com/api/v2/epayment/lookup/",
        headers=headers,
        data=json.dumps(payload)
    )

    if response.status_code != 200:
        messages.error(request, "Payment verification failed.")
        return redirect("attendance:my_fees")

    data = response.json()
    payment_status = data.get("status")

    # Payment success
    if payment_status == "Completed":
        # Prevent duplicate Payment rows
        if khalti_payment.status != "COMPLETED":
            khalti_payment.status = "COMPLETED"
            khalti_payment.transaction_id = data.get("transaction_id")
            khalti_payment.completed_at = timezone.now()
            khalti_payment.save()

            Payment.objects.create(
                student=khalti_payment.student,
                semester=khalti_payment.semester,
                amount=khalti_payment.amount,
                note="Paid via Khalti",
                payment_method="KHALTI",
                status="COMPLETED",
                pidx=khalti_payment.pidx,
                transaction_id=khalti_payment.transaction_id,
                purchase_order_id=khalti_payment.purchase_order_id,
            )

            Notification.objects.create(
                student=khalti_payment.student,
                title="Fee Payment Successful",
                message=f"Your Khalti payment of Rs {khalti_payment.amount} was successful.",
                amount=khalti_payment.amount,
                status="SENT",
            )

        messages.success(request, "Payment completed successfully.")
    else:
        khalti_payment.status = "FAILED"
        khalti_payment.save()
        messages.error(request, f"Payment not completed. Status: {payment_status}")

    return redirect("attendance:my_fees")
    
@login_required
def teacher_student_detail(request, student_id):
    student = get_object_or_404(User, id=student_id)
    records = AttendanceRecord.objects.filter(student=student).order_by('-date', '-recorded_at')

    return render(request, "attendance/teacher_student_detail.html", {
        "student": student,
        "records": records,
    }) 
@login_required
def teacher_edit_attendance(request, student_id):
    student = get_object_or_404(User, id=student_id)
    record = AttendanceRecord.objects.filter(student=student).order_by('-date', '-recorded_at').first()

    if request.method == "POST":
        new_status = request.POST.get("status")
        if record and new_status in ["Present", "Absent"]:
            record.status = new_status
            record.save()
        return redirect("attendance:teacher_students")

    return render(request, "attendance/teacher_edit_attendance.html", {
        "student": student,
        "record": record,
    })
@login_required
def teacher_attendance_history(request, student_id):
    student = get_object_or_404(User, id=student_id)
    history = AttendanceRecord.objects.filter(student=student).order_by('-date', '-recorded_at')

    return render(request, "attendance/teacher_attendance_history.html", {
        "student": student,
        "history": history,
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

from .models import Subject, AttendanceRecord, FeeStructure, Payment, Notification, StudentProfile


@login_required
def student_dashboard(request):
    print("LOGGED IN USER:", request.user.username)

    if not hasattr(request.user, "profile") or request.user.profile.role != "student":
        messages.error(request, "Students only.")
        return redirect("home")

    profile, created = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.get_full_name() or request.user.username,
            "student_id": f"STD-{request.user.id}",
        }
    )

    enrolled_subjects = Subject.objects.filter(students=request.user)

    attendance_stats = []
    total_classes_all = 0
    total_present_all = 0

    for subject in enrolled_subjects:
        total = AttendanceRecord.objects.filter(
            student=request.user,
            subject=subject
        ).count()

        present = AttendanceRecord.objects.filter(
            student=request.user,
            subject=subject,
            status="Present"
        ).count()

        percent = round((present / total) * 100, 2) if total else 0

        total_classes_all += total
        total_present_all += present

        attendance_stats.append({
            "subject": subject,
            "total": total,
            "present": present,
            "percentage": percent,
        })

    attendance_records = AttendanceRecord.objects.filter(
        student=request.user
    ).select_related("subject").order_by("-id")[:10]

    today = timezone.localdate()
    due_soon_date = today + timedelta(days=7)

    fee_total = 0
    fee_paid = 0
    fee_remaining = 0
    fee_percent = 0
    fee_due_date = None
    popup_notification = None

    fee = FeeStructure.objects.filter(student=profile).order_by("-semester").first()

    if fee:
        fee_total = float(fee.total_fee)
        fee_due_date = fee.due_date

        fee_paid = Payment.objects.filter(
            student=profile,
            semester=fee.semester,
            status="COMPLETED"
        ).aggregate(total=Sum("amount"))["total"] or 0

        fee_paid = float(fee_paid)
        fee_remaining = max(fee_total - fee_paid, 0)
        fee_percent = int((fee_paid / fee_total) * 100) if fee_total else 0

        if fee_due_date and fee_remaining > 0 and today <= fee_due_date <= due_soon_date:
            title = "Fee Due Reminder"
            msg = f"Your remaining fee is Rs. {fee_remaining} and due on {fee_due_date}. Please pay before deadline."

            Notification.objects.update_or_create(
                student=profile,
                title=title,
                is_read=False,
                defaults={
                    "message": msg,
                    "amount": fee_remaining,
                    "status": "PENDING",
                }
            )

        popup_notification = Notification.objects.filter(
            student=profile,
            is_read=False
        ).order_by("-created_at").first()

    # =========================
    # Activity Timeline
    # =========================
    timeline = []

    payment_items = Payment.objects.filter(
        student=profile,
        status="COMPLETED"
    ).order_by("-paid_at")

    for p in payment_items:
        timeline.append({
            "title": "Fee Payment",
            "desc": f"Paid Rs. {p.amount} via {p.payment_method or 'payment'}",
            "date": p.paid_at,
            "type": "payment",
        })

    attendance_items = AttendanceRecord.objects.filter(
        student=request.user
    ).select_related("subject").order_by("-date", "-recorded_at")

    for a in attendance_items:
        timeline.append({
            "title": "Attendance",
            "desc": f"{a.status} in {a.subject.name}",
            "date": a.recorded_at or a.date,
            "type": "attendance",
        })

    notification_items = Notification.objects.filter(
        student=profile
    ).order_by("-created_at")

    for n in notification_items:
        timeline.append({
            "title": n.title,
            "desc": n.message,
            "date": n.created_at,
            "type": "notification",
        })

    timeline = sorted(timeline, key=lambda x: x["date"], reverse=True)[:12]

    return render(request, "attendance/student_dashboard.html", {
        "profile": profile,
        "attendance_stats": attendance_stats,
        "attendance_records": attendance_records,
        "total_classes_all": total_classes_all,
        "total_present_all": total_present_all,
        "fee_total": fee_total,
        "fee_paid": fee_paid,
        "fee_remaining": fee_remaining,
        "fee_percent": fee_percent,
        "fee_due_date": fee_due_date,
        "popup_notification": popup_notification,
        "timeline": timeline,
    })
@login_required
@user_passes_test(fee_manager_only)
def fee_structures_page(request):
    query = request.GET.get("q", "")
    semester = request.GET.get("semester", "")

    fee_structures = FeeStructure.objects.select_related("student").all().order_by("student__full_name")

    if query:
        fee_structures = fee_structures.filter(
            Q(student__full_name__icontains=query) |
            Q(student__student_id__icontains=query)
        )

    if semester:
        fee_structures = fee_structures.filter(semester=semester)

    semesters = FeeStructure.objects.values_list("semester", flat=True).distinct().order_by("semester")

    context = {
        "fee_structures": fee_structures,
        "query": query,
        "semesters": semesters,
        "selected_semester": semester,
        "total_count": fee_structures.count(),
    }
    return render(request, "attendance/fee_structures.html", context)


@login_required
@user_passes_test(fee_manager_only)
def add_fee_structure(request):
    if request.method == "POST":
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee structure added successfully.")
            return redirect("attendance:fee_structures_page")
    else:
        form = FeeStructureForm()

    return render(request, "attendance/fee_structure_form.html", {
        "form": form,
        "page_title": "Add Fee Structure"
    })


@login_required
@user_passes_test(fee_manager_only)
def edit_fee_structure(request, pk):
    fee_structure = get_object_or_404(FeeStructure, pk=pk)

    if request.method == "POST":
        form = FeeStructureForm(request.POST, instance=fee_structure)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee structure updated successfully.")
            return redirect("attendance:fee_structures_page")
    else:
        form = FeeStructureForm(instance=fee_structure)

    return render(request, "attendance/fee_structure_form.html", {
        "form": form,
        "page_title": "Edit Fee Structure",
        "fee_structure": fee_structure
    })


@login_required
@user_passes_test(fee_manager_only)
def delete_fee_structure(request, pk):
    fee_structure = get_object_or_404(FeeStructure, pk=pk)

    if request.method == "POST":
        fee_structure.delete()
        messages.success(request, "Fee structure deleted successfully.")
        return redirect("attendance:fee_structures_page")

    return render(request, "attendance/delete_fee_structure.html", {
        "fee_structure": fee_structure
    })

@login_required
def fee_payments_page(request):
    if not request.user.groups.filter(name="feesmanager").exists() and not request.user.is_superuser:
        messages.error(request, "Fee managers only.")
        return redirect("home")

    payments = Payment.objects.select_related("student").order_by("-paid_at")

    return render(request, "attendance/fee_payments.html", {
        "payments": payments,
    })
import requests
from django.conf import settings
from django.urls import reverse

@login_required
def khalti_initiate(request):
    profile = StudentProfile.objects.filter(user=request.user).first()
    if not profile:
        messages.error(request, "Student profile not found.")
        return redirect("attendance:student_my_fees")

    fee_structure = FeeStructure.objects.filter(student=profile).order_by("-semester").first()
    if not fee_structure:
        messages.error(request, "Fee structure not found.")
        return redirect("attendance:student_my_fees")

    paid_amount = Payment.objects.filter(student=profile, semester=fee_structure.semester).aggregate(
        total=Sum("amount")
    )["total"] or 0

    remaining = fee_structure.total_fee - paid_amount

    if remaining <= 0:
        messages.info(request, "No remaining fee to pay.")
        return redirect("attendance:student_my_fees")

    purchase_order_id = f"FEE-{request.user.id}-{timezone.now().timestamp()}"
    return_url = request.build_absolute_uri(reverse("attendance:khalti_verify"))

    payload = {
        "return_url": return_url,
        "website_url": settings.KHALTI_WEBSITE_URL,
        "amount": int(remaining * 100),  # paisa
        "purchase_order_id": purchase_order_id,
        "purchase_order_name": f"Semester {fee_structure.semester} Fee",
        "customer_info": {
            "name": profile.full_name or request.user.username,
            "email": request.user.email or "student@example.com",
            "phone": "9800000001",
        },
    }

    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://dev.khalti.com/api/v2/epayment/initiate/",
        json=payload,
        headers=headers,
    )

    data = response.json()

    if response.status_code != 200:
        messages.error(request, f"Khalti initiate failed: {data}")
        return redirect("attendance:student_my_fees")

    KhaltiPayment.objects.create(
        student=profile,
        semester=fee_structure.semester,
        amount=remaining,
        purchase_order_id=purchase_order_id,
        pidx=data.get("pidx"),
        status="INITIATED",
    )

    return redirect(data["payment_url"])


@login_required
def khalti_verify(request):
    pidx = request.GET.get("pidx")
    if not pidx:
        messages.error(request, "Missing Khalti payment reference.")
        return redirect("attendance:student_my_fees")

    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://dev.khalti.com/api/v2/epayment/lookup/",
        json={"pidx": pidx},
        headers=headers,
    )

    data = response.json()

    if response.status_code != 200:
        messages.error(request, "Payment verification failed.")
        return redirect("attendance:student_my_fees")

    khalti_payment = KhaltiPayment.objects.filter(pidx=pidx).first()
    if not khalti_payment:
        messages.error(request, "Khalti payment record not found.")
        return redirect("attendance:student_my_fees")

    if data.get("status") == "Completed":
        khalti_payment.status = "COMPLETED"
        khalti_payment.save()

        already_exists = Payment.objects.filter(
            student=khalti_payment.student,
            semester=khalti_payment.semester,
            note__icontains=khalti_payment.purchase_order_id,
        ).exists()

        if not already_exists:
            Payment.objects.create(
                student=khalti_payment.student,
                semester=khalti_payment.semester,
                amount=khalti_payment.amount,
                note=f"Khalti payment ({khalti_payment.purchase_order_id})",
            )

        messages.success(request, "Fee payment completed successfully.")
    else:
        khalti_payment.status = data.get("status", "FAILED")
        khalti_payment.save()
        messages.error(request, f"Payment not completed. Status: {data.get('status')}")

    return redirect("attendance:student_my_fees")