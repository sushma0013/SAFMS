from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import messages
from .models import QRSession, AttendanceRecord, Subject
from datetime import timedelta
from .utils import close_session_and_mark_absent
from datetime import timedelta
from django.db.models import Count,Q
from django.contrib.auth.models import User
from .models import StudentProfile






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
@login_required
def student_dashboard(request):
    if request.user.profile.role != 'student':
        messages.error(request, "Students only.")
        return redirect('home')

    enrolled_subjects = Subject.objects.filter(students=request.user)

    attendance_stats = []

    for subject in enrolled_subjects:
        total = AttendanceRecord.objects.filter(
            student=request.user, subject=subject
        ).count()

        present = AttendanceRecord.objects.filter(
            student=request.user, subject=subject, status='Present'
        ).count()

        percent = round((present / total) * 100, 2) if total else 0

        attendance_stats.append({
            'subject': subject,
            'total': total,
            'present': present,
            'percentage': percent
        })

    return render(request, 'attendance/student_dashboard.html', {
        'enrolled_subjects': enrolled_subjects,
        'attendance_stats': attendance_stats,
    })
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

            return redirect("attendance:student_dashboard")

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







