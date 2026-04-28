from django.utils import timezone
from .models import AttendanceRecord
from ipaddress import ip_address, ip_network


def close_session_and_mark_absent(session):
    """
    Mark absent students when session closes.
    """
    students = session.subject.students.all()

    for student in students:
        AttendanceRecord.objects.get_or_create(
            student=student,
            session=session,
            subject=session.subject,
            defaults={"status": "Absent"}
        )

    session.is_closed = True
    session.closed_at = timezone.now()
    session.save()


def get_client_ip(request):
    """
    Get real client IP.
    Works with localhost, WiFi and ngrok.
    """
    candidate_headers = [
        "HTTP_CF_CONNECTING_IP",
        "HTTP_TRUE_CLIENT_IP",
        "HTTP_X_REAL_IP",
        "HTTP_X_FORWARDED_FOR",
        "REMOTE_ADDR",
    ]

    for header in candidate_headers:
        raw_value = request.META.get(header)
        if not raw_value:
            continue

        # X-Forwarded-For may contain comma-separated IP chain.
        first_candidate = raw_value.split(",")[0].strip()

        try:
            return str(ip_address(first_candidate))
        except ValueError:
            continue

    return ""


def is_public_ip(ip_str):
    """
    Return True only for globally routable IPs.
    """
    try:
        return ip_address(ip_str).is_global
    except ValueError:
        return False


def same_network(ip1, ip2):
    """
    Check if both IPs are in same local network.
    Example:
    192.168.1.10
    192.168.1.22
    """
    try:
        net1 = ".".join(ip1.split(".")[:3])
        net2 = ".".join(ip2.split(".")[:3])
        return net1 == net2
    except:
        return False


def ip_in_allowed_network(ip_str, network_str):
    """
    Check if IP is inside given CIDR network.
    """
    try:
        return ip_address(ip_str) in ip_network(network_str, strict=False)
    except ValueError:
        return False


def parse_student_semester(profile):
    """Return student's current semester as int. Defaults to 1 if missing/invalid."""
    if not profile:
        return 1
    raw = (profile.semester or "").strip()
    if raw.isdigit():
        return int(raw)
    # also handle '1st', '2nd', etc.
    digits = "".join(ch for ch in raw if ch.isdigit())
    return int(digits) if digits else 1