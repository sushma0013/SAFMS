from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import messages
from .models import QRSession, AttendanceRecord, Subject
from datetime import timedelta
from .utils import close_session_and_mark_absent

from django.db.models import Count,Q
from django.contrib.auth.models import User
from .models import StudentProfile
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import StudentProfile, FeeStructure, Payment

from django.db.models import Sum
from django.db.models import Sum
from datetime import timedelta
from .models import StudentProfile, FeeStructure, Payment, Notification
















NGROK_BASE_URL = "https://sericultural-undefiable-davina.ngrok-free.dev"









# ============= TEACHER VIEWS =============

@login_required
def teacher_dashboard(request):
    # -------------------------
    # ROLE CHECK
    # -------------------------
    if request.user.profile.role != 'teacher':
        messages.error(request, "Teachers only.")
        return redirect('home')

    # -------------------------
    # AUTO-CLOSE EXPIRED QR
    # -------------------------
    now = timezone.now()
    expired_sessions = QRSession.objects.filter(
        created_by=request.user,
        is_closed=False,
        valid_until__lte=now
    )

    for session in expired_sessions:
        close_session_and_mark_absent(session)

    # -------------------------
    # NORMAL DASHBOARD LOGIC
    # -------------------------
    subjects = Subject.objects.filter(teacher=request.user)
    today = timezone.now().date()

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

        today_present += present
        today_total += total_students

        subject_stats.append({
            'subject': subject,
            'total': total_students,
            'present': present,
        })

    attendance_today = round(
        (today_present / today_total) * 100, 2
    ) if today_total else 0

    # -------------------------
    # LOW ATTENDANCE (<80%)
    # -------------------------
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
            percentage = (present_classes / total_classes) * 100
            if percentage < 80:
                low_attendance_students.append({
                    'student': User.objects.get(id=student_id),
                    'percentage': round(percentage, 2)
                })

    return render(request, 'attendance/teacher_dashboard.html', {
        'subjects': subjects,
        'subject_stats': subject_stats,
        'attendance_today': attendance_today,
        'low_attendance_students': low_attendance_students,
    })

# @login_required
# def teacher_dashboard(request):
#     if request.user.profile.role != 'teacher':
#         messages.error(request, "Teachers only.")
#         return redirect('home')

#     subjects = Subject.objects.filter(teacher=request.user)
#     today = timezone.now().date()

#     subject_stats = []
#     today_present = 0
#     today_total = 0

#     # =========================
#     # SUBJECT LOOP
#     # =========================
#     for subject in subjects:
#         total_students = subject.students.count()

#         session = QRSession.objects.filter(
#             subject=subject,
#             session_date=today
#         ).order_by('-created_at').first()

#         if session:
#             present = AttendanceRecord.objects.filter(
#                 session=session,
#                 status='Present'
#             ).count()
#         else:
#             present = 0

#         today_present += present
#         today_total += total_students

#         subject_stats.append({
#             'subject': subject,
#             'total': total_students,
#             'present': present,
#         })

#     # =========================
#     # TODAY ATTENDANCE %
#     # =========================
#     attendance_today = round(
#         (today_present / today_total) * 100, 2
#     ) if today_total else 0

#     # =========================
#     # STUDENTS BELOW 80%
#     # =========================
#     low_attendance_students = []

#     students = AttendanceRecord.objects.filter(
#         subject__teacher=request.user
#     ).values('student').distinct()

#     for s in students:
#         student_id = s['student']

#         total_classes = AttendanceRecord.objects.filter(
#             student_id=student_id,
#             subject__teacher=request.user
#         ).count()

#         present_classes = AttendanceRecord.objects.filter(
#             student_id=student_id,
#             subject__teacher=request.user,
#             status='Present'
#         ).count()

#         if total_classes > 0:
#             percentage = (present_classes / total_classes) * 100
#             if percentage < 80:
#                 low_attendance_students.append({
#                     'student': User.objects.get(id=student_id),
#                     'percentage': round(percentage, 2)
#                 })
                

#     # =========================
#     # FINAL RETURN
#     # =========================
#     return render(request, 'attendance/teacher_dashboard.html', {
#         'subjects': subjects,
#         'subject_stats': subject_stats,
#         'attendance_today': attendance_today,
#         'low_attendance_students': low_attendance_students,
#     })




@login_required
def generate_qr(request, subject_id):
    if request.user.profile.role != 'teacher':
        messages.error(request, "Teachers only.")
        return redirect('home')

    subject = get_object_or_404(Subject, id=subject_id, teacher=request.user)
    now = timezone.now()
    today = now.date()

    # 1) Find active session for this subject today
    active_session = QRSession.objects.filter(
        subject=subject,
        created_by=request.user,
        session_date=today,
        is_closed=False,
        valid_until__gt=now
    ).order_by('-created_at').first()

    if active_session:
        session = active_session
        messages.info(request, "Using existing active QR session.")
    else:
        # 2) If there is an old session expired but not closed -> close it & mark absent
        old_open_sessions = QRSession.objects.filter(
            subject=subject,
            created_by=request.user,
            session_date=today,
            is_closed=False,
            valid_until__lte=now
        )
        for s in old_open_sessions:
            close_session_and_mark_absent(s)

        # 3) Create new session
        session = QRSession.objects.create(
            subject=subject,
            created_by=request.user,
            session_date=today,
            valid_until=now + timedelta(minutes=15),
            is_closed=False
        )
        session.generate_qr(request_domain=NGROK_BASE_URL)
        messages.success(request, "New QR generated (valid 15 minutes).")

    return render(request, 'attendance/generate_qr.html', {
        'session': session,
        'subject': subject,
        'expires_in': int((session.valid_until - now).total_seconds())
    })


# ============= STUDENT VIEWS =============


# @login_required
# def student_dashboard(request):
#     if request.user.profile.role != 'student':
#         messages.error(request, "Students only.")
#         return redirect('home')

#     enrolled_subjects = Subject.objects.filter(students=request.user)

#     attendance_stats = []
#     total_classes_all = 0
#     total_present_all = 0

#     for subject in enrolled_subjects:
#         total = AttendanceRecord.objects.filter(student=request.user, subject=subject).count()
#         present = AttendanceRecord.objects.filter(student=request.user, subject=subject, status='Present').count()
#         percent = round((present / total) * 100, 2) if total else 0

#         total_classes_all += total
#         total_present_all += present

#         attendance_stats.append({
#             'subject': subject,
#             'total': total,
#             'present': present,
#             'percentage': percent
#         })

#     attendance_records = AttendanceRecord.objects.filter(
#         student=request.user
#     ).select_related('subject').order_by('-id')[:10]

#     return render(request, 'attendance/student_dashboard.html', {
#         'enrolled_subjects': enrolled_subjects,
#         'attendance_stats': attendance_stats,
#         'attendance_records': attendance_records,
#         'total_classes_all': total_classes_all,
#         'total_present_all': total_present_all,
#     })
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

@login_required
def student_dashboard(request):
    if request.user.profile.role != "student":
        messages.error(request, "Students only.")
        return redirect("home")

    # ✅ get StudentProfile of logged-in student
    try:
        profile = request.user.student_profile  # related_name="student_profile"
    except StudentProfile.DoesNotExist:
        messages.error(request, "Your student profile is not linked. Contact admin.")
        return redirect("home")

    # ==============================
    # ✅ ATTENDANCE DATA
    # ==============================
    enrolled_subjects = Subject.objects.filter(students=request.user)

    attendance_stats = []
    total_classes_all = 0
    total_present_all = 0

    for subject in enrolled_subjects:
        total = AttendanceRecord.objects.filter(student=request.user, subject=subject).count()
        present = AttendanceRecord.objects.filter(student=request.user, subject=subject, status="Present").count()
        percent = round((present / total) * 100, 2) if total else 0

        total_classes_all += total
        total_present_all += present

        attendance_stats.append({
            "subject": subject,
            "total": total,
            "present": present,
            "percentage": percent
        })

    attendance_records = (
        AttendanceRecord.objects.filter(student=request.user)
        .select_related("subject")
        .order_by("-id")[:10]
    )

    # ==============================
    # ✅ FEE SUMMARY + POPUP NOTIFICATION
    # ==============================
    today = timezone.localdate()
    due_soon_date = today + timedelta(days=7)

    # defaults (so template never crashes)
    fee_total = 0.0
    fee_paid = 0.0
    fee_remaining = 0.0
    fee_due_date = None
    fee_percent = 0
    popup_notification = None

    fee = FeeStructure.objects.filter(student=profile).order_by("-semester").first()

    if fee:
        fee_total = float(fee.total_fee)
        fee_due_date = fee.due_date

        fee_paid = Payment.objects.filter(student=profile, semester=fee.semester).aggregate(
            total=Sum("amount")
        )["total"] or 0
        fee_paid = float(fee_paid)

        fee_remaining = max(fee_total - fee_paid, 0)
        fee_percent = int((fee_paid / fee_total) * 100) if fee_total > 0 else 0

        # ✅ create/update popup reminder only if due soon AND still remaining
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
                is_read=False,
                title=title
            ).order_by("-created_at").first()

    return render(request, "attendance/student_dashboard.html", {
        "profile": profile,
        "enrolled_subjects": enrolled_subjects,
        "attendance_stats": attendance_stats,
        "attendance_records": attendance_records,
        "total_classes_all": total_classes_all,
        "total_present_all": total_present_all,

        # ✅ fee values for dashboard cards
        "fee_total": fee_total,
        "fee_paid": fee_paid,
        "fee_remaining": fee_remaining,
        "fee_due_date": fee_due_date,
        "fee_percent": fee_percent,

        # ✅ popup notification
        "popup_notification": popup_notification,
    })


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





@login_required
def mark_attendance(request, uuid):
    if request.user.profile.role != 'student':
        return HttpResponse("Access denied")

    session = get_object_or_404(QRSession, uuid=uuid)

    # expired or closed session
    if session.valid_until < timezone.now() or session.is_closed:
        if not session.is_closed:
            close_session_and_mark_absent(session)
        return render(request, 'attendance/qr_expired.html')

    # enrolled check
    if not session.subject.students.filter(id=request.user.id).exists():
        return HttpResponse("Not enrolled in this subject")

    # if record exists already
    record = AttendanceRecord.objects.filter(student=request.user, session=session).first()
    if record:
        return render(request, 'attendance/already_marked.html')

    # mark present
    AttendanceRecord.objects.create(
        student=request.user,
        session=session,
        subject=session.subject,
        status='Present'
    )

    return render(request, 'attendance/success.html', {'subject': session.subject})


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

    return render(request, "attendance/my_classes.html", {
        "sessions_today": sessions_today,
        "today": today,
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
    return render(request, "attendance/teacher_reports.html")

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
        messages.success(request, f"{student.username} enrolled in {subject.code}.")
        return redirect("attendance:teacher_students")

    return render(request, "attendance/teacher_add_student.html", {"subjects": subjects})

# @login_required
# def student_profile(request):
#     if request.user.profile.role != "student":
#         messages.error(request, "Students only.")
#         return redirect("home")

#     try:
#         profile = StudentProfile.objects.get(user=request.user)
#     except StudentProfile.DoesNotExist:
#         messages.error(request, "Student profile not found. Ask admin to create/link it.")
#         return redirect("attendance:student_dashboard")

#     total = AttendanceRecord.objects.filter(student=request.user).count()
#     present = AttendanceRecord.objects.filter(student=request.user, status="Present").count()
#     attendance_percent = round((present / total) * 100, 2) if total else 0

#     return render(request, "attendance/student_profile.html", {
#         "profile": profile,
#         "attendance_percent": attendance_percent,
#     })


@login_required
def my_attendance(request):
    if request.user.profile.role != 'student':
        messages.error(request, "Students only.")
        return redirect('home')
    return render(request, "attendance/my_attendance.html")



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
        semester=current_semester
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


@login_required
def student_report(request):
    if request.user.profile.role != 'student':
        messages.error(request, "Students only.")
        return redirect('home')
    return render(request, "attendance/student_report.html")


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

def staff_only(user):
    return user.is_staff  # fee manager must be staff

@login_required
@user_passes_test(staff_only)
def fee_manager_dashboard(request):
    total_students = StudentProfile.objects.count()
    total_fee_set = FeeStructure.objects.count()

    total_collected = Payment.objects.aggregate(total=Sum("amount"))["total"] or 0

    # Students with due (total_fee - paid > 0)
    # Simple approximation: count students where paid < total_fee
    fee_rows = FeeStructure.objects.select_related("student").all()
    due_students = 0
    due_soon_students = 0

    today = timezone.localdate()
    due_soon_date = today + timedelta(days=7)

    for fee in fee_rows:
        paid = fee.student.payments.aggregate(total=Sum("amount"))["total"] or 0
        remaining = fee.total_fee - paid
        if remaining > 0:
            due_students += 1
            if fee.due_date and today <= fee.due_date <= due_soon_date:
                due_soon_students += 1

    recent_payments = Payment.objects.select_related("student").order_by("-paid_at")[:8]

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

@login_required
def create_payment_request(request):
    if request.user.profile.role != "student":
        messages.error(request, "Students only.")
        return redirect("home")

    student = get_object_or_404(StudentProfile, user=request.user)

    if request.method == "POST":
        semester = int(request.POST.get("semester", 1))
        amount = request.POST.get("amount")
        note = request.POST.get("note", "")
        proof = request.FILES.get("proof")

        PaymentRequest.objects.create(
            student=student,
            semester=semester,
            amount=amount,
            note=note,
            proof=proof,
            status="PENDING",
        )

        messages.success(request, "Payment request submitted. Waiting for approval.")
        return redirect("attendance:my_fees")

    return render(request, "attendance/payment_request_form.html")


def staff_only(user):
    return user.is_staff

@login_required
@user_passes_test(staff_only)
def fee_manager_requests(request):
    requests = PaymentRequest.objects.select_related("student").order_by("-created_at")
    return render(request, "attendance/fee_manager_requests.html", {"requests": requests})


@login_required
@user_passes_test(staff_only)
def approve_payment_request(request, pk):
    pr = get_object_or_404(PaymentRequest, pk=pk)

    if pr.status != "PENDING":
        messages.info(request, "Already reviewed.")
        return redirect("attendance:fee_manager_requests")

    # ✅ Create Payment automatically
    Payment.objects.create(
        student=pr.student,
        semester=pr.semester,
        amount=pr.amount,
        note=f"Approved: {pr.note}",
    )

    pr.status = "APPROVED"
    pr.reviewed_by = request.user
    pr.reviewed_at = timezone.now()
    pr.save()

    Notification.objects.create(
        student=pr.student,
        title="Payment Approved",
        message=f"Your payment of Rs {pr.amount} has been approved.",
        amount=pr.amount,
        status="SENT",
    )

    messages.success(request, "Approved and added to Payments.")
    return redirect("attendance:fee_manager_requests")


@login_required
@user_passes_test(staff_only)
def reject_payment_request(request, pk):
    pr = get_object_or_404(PaymentRequest, pk=pk)

    pr.status = "REJECTED"
    pr.reviewed_by = request.user
    pr.reviewed_at = timezone.now()
    pr.save()

    Notification.objects.create(
        student=pr.student,
        title="Payment Rejected",
        message="Your payment proof was rejected. Please submit again with correct details.",
        status="SENT",
    )

    messages.error(request, "Rejected.")
    return redirect("attendance:fee_manager_requests")

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



