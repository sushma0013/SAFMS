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
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")

    return ip


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