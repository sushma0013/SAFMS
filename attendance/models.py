
from django.db import models
from django.contrib.auth.models import User
import qrcode
from io import BytesIO
from django.core.files import File
from django.utils import timezone
import uuid
import os
from datetime import timedelta

def qr_upload_path(instance, filename):
    return os.path.join('qr_codes', filename)

# ------------------------------------------------------------
# Subject Model
# ------------------------------------------------------------
# Subject Model
class Subject(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20, unique=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subjects')
    students = models.ManyToManyField(User, related_name='enrolled_subjects', blank=True)
    semester = models.IntegerField(default=1)
    department = models.CharField(max_length=100, default='General')

    def __str__(self):
        return f"{self.code} - {self.name} ({self.teacher.username})"
    
    def total_students(self):
        return self.students.count()


# ------------------------------------------------------------
# QRSession Model (UPDATED)
# ------------------------------------------------------------
class QRSession(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    session_date = models.DateField(default=timezone.now)  # <--- Set default today
    valid_until = models.DateTimeField(blank=True, null=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    is_closed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.valid_until:
            self.valid_until = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)

    def __str__(self):
    # Check if session_date is datetime or date
    #  if hasattr(self.session_date, 'date'):  # if datetime
    #     session_str = self.session_date.date()
    #  else:  # already a date
    #     session_str = self.session_date
     return f"{self.subject.name} - {self.session_date}"


    # Method to generate the QR Code
    def generate_qr(self, request_domain=None):
        # Build absolute URL
        if request_domain:
            url = f"{request_domain}/attendance/mark/{self.uuid}/"
        else:
            url = f"/attendance/mark/{self.uuid}/"

        img = qrcode.make(url)

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        filename = f"qr_{self.uuid}.png"
        self.qr_code.save(filename, File(buffer), save=False)
        buffer.close()

        self.save()


# ------------------------------------------------------------
# AttendanceRecord Model
# ------------------------------------------------------------
# class AttendanceRecord(models.Model):
#     student = models.ForeignKey(User, on_delete=models.CASCADE)
#     session = models.ForeignKey(QRSession, on_delete=models.CASCADE, related_name='attendance_records')
#     subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

#     STATUS_CHOICES = (
#         ('Present', 'Present'),
#         ('Absent', 'Absent'),
#     )

#     status = models.CharField(
#     max_length=10,
#     choices=(('Present','Present'), ('Absent','Absent')),
#     default='Absent'
# )

# recorded_at = models.DateTimeField(auto_now_add=True)


# class Meta:
#         unique_together = ('student', 'session')

# def __str__(self):
#         return f"{self.student.username} - {self.subject.code} - {self.status}"

class AttendanceRecord(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(QRSession, on_delete=models.CASCADE, related_name='attendance_records')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    STATUS_CHOICES = (
        ('Present', 'Present'),
        ('Absent', 'Absent'),
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Absent')
    date = models.DateField(auto_now_add=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'session')

