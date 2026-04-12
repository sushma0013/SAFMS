# This ensures everyone gets a record, even if they don’t scan.
from django.utils import timezone
from .models import AttendanceRecord

def close_session_and_mark_absent(session):
    # Create Absent record for every enrolled student not present
    students = session.subject.students.all()

    for student in students:
        AttendanceRecord.objects.get_or_create(
            student=student,
            session=session,
            subject=session.subject,
            defaults={'status': 'Absent'}
        )

    session.is_closed = True
    session.closed_at = timezone.now()
    session.save()

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")
