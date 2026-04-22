# This ensures everyone gets a record, even if they don’t scan.
from django.utils import timezone
from .models import AttendanceRecord
from ipaddress import ip_address, ip_network


def _iter_allowed_networks(network_spec):
    """
    Yield one or more network definitions from a string.

    Supports a single CIDR like "110.34.30.0/24" or a comma-separated list
    like "110.34.30.0/24, 10.0.0.0/8".
    """
    if not network_spec:
        return

    for raw_network in str(network_spec).split(","):
        network = raw_network.strip()
        if network:
            yield network

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

# def get_client_ip(request):
#     x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
#     if x_forwarded_for:
#         return x_forwarded_for.split(",")[0].strip()
#     return request.META.get("REMOTE_ADDR", "")


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def ip_in_allowed_network(ip_str, network_str):
    """
    Example:
    ip_str = '10.22.12.155'
    network_str = '10.22.0.0/19'
    """
    try:
        return any(
            ip_address(ip_str) in ip_network(network, strict=False)
            for network in _iter_allowed_networks(network_str)
        )
    except ValueError:
        return False


def same_network(ip1, ip2, network_str):
    """
    True if both IPs fall inside the same allowed network.
    """
    try:
        return any(
            ip_address(ip1) in net and ip_address(ip2) in net
            for net in (ip_network(network, strict=False) for network in _iter_allowed_networks(network_str))
        )
    except ValueError:
        return False