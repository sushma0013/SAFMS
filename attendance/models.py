
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
    closed_at = models.DateTimeField(null=True, blank=True)

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

    def __str__(self):
        return f"{self.student.username} - {self.subject.code} - {self.status}"


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )

    student_id = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=100)

    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)

    major = models.CharField(max_length=60, blank=True)
    semester = models.CharField(max_length=30, blank=True)

    academic_advisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="advised_students"
    )

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"
# class AttendanceRecord(models.Model):
#     student = models.ForeignKey(User, on_delete=models.CASCADE)
#     session = models.ForeignKey(QRSession, on_delete=models.CASCADE, related_name='attendance_records')
#     subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

#     STATUS_CHOICES = (
#         ('Present', 'Present'),
#         ('Absent', 'Absent'),
#     )

#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Absent')
#     date = models.DateField(auto_now_add=True)
#     recorded_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('student', 'session')

#         class StudentProfile(models.Model):
#           user = models.OneToOneField(
#         User,
#         on_delete=models.CASCADE,
#         related_name="student_profile"
#     )

#     # Basic student info
#     student_id = models.CharField(max_length=30, unique=True)
#     full_name = models.CharField(max_length=100)

#     phone = models.CharField(max_length=20, blank=True)
#     address = models.CharField(max_length=255, blank=True)

#     major = models.CharField(max_length=60, blank=True)        # Math, Science, CS...
#     semester = models.CharField(max_length=30, blank=True)     # "5th Semester"

#     # advisor can be teacher User (best + not complicated)
#     academic_advisor = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="advised_students"
#     )

#     def __str__(self):
#         return f"{self.student_id} - {self.full_name}"

# class StudentProfile(models.Model):
#     user = models.OneToOneField(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="attendance_student"
#     )

#     student_id = models.PositiveIntegerField(unique=True)
#     full_name = models.CharField(max_length=100)

#     def __str__(self):
#         return f"{self.student_id} - {self.full_name}"




class FeeStructure(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="fee_structures")
    semester = models.PositiveIntegerField(default=1)  # ✅ default added
    total_fee = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("student", "semester")  # ✅ one fee row per student per semester

    def __str__(self):
        return f"{self.student.full_name} | Sem {self.semester}"


class Payment(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="payments"
    )
    semester = models.PositiveIntegerField(default=1)  # ✅ default added
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} | Rs {self.amount}"


class Notification(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("SENT", "Sent"),
        ("READ", "Read"),
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(max_length=120)
    message = models.TextField()

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.student_id} - {self.title}"


class PaymentRequest(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="payment_requests"
    )
    semester = models.IntegerField(default=1)  # ✅ add default to avoid migration prompt
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)

    proof = models.ImageField(upload_to="payment_proofs/", null=True, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_payments"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.student_id} | {self.amount} | {self.status}"