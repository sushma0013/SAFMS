# attendance/models.py
# ----------------------
# This file defines all database models (tables) used in the Attendance system.
# Each class here will become a table in the SQLite / MySQL database.

from django.db import models
from django.contrib.auth.models import User
import qrcode                     # library for generating QR images
from io import BytesIO             # to store image data temporarily in memory
from django.core.files import File # to save the image into Django's ImageField
from django.utils import timezone  # for getting the current date/time
import os
# ------------------------------------------------------------
# 🧩 Subject Model
# ------------------------------------------------------------
class Subject(models.Model):
    # The name of the subject (like "Math" or "English")
    name = models.CharField(max_length=120)

    # The teacher who teaches this subject (linked to the built-in User table)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)

    # This function helps Django show a readable name in admin panel
    def __str__(self):
        return f"{self.name} ({self.teacher.username})"


# ------------------------------------------------------------
# 🧩 QRSession Model
# ------------------------------------------------------------
# Each QRSession represents one class session (for example:
# "Math class on 2025-11-13" that has a unique QR code for attendance)
class QRSession(models.Model):
    # Link this session to a specific subject
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    # Automatically use today’s date for the session (you can also set manually)
    date = models.DateField(default=timezone.now)

    # Store the teacher who generated this QR (important for tracking)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, default=1)

    # Timestamp — Django auto-fills this when the record is created
    created_at = models.DateTimeField(auto_now_add=True)

    # Store the generated QR image in 'media/qr_codes/' folder
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    # Show a readable name (example: "Math - 2025-11-13")
    def __str__(self):
        return f"{self.subject.name} - {self.teacher.username} ({self.date})"

    # The save() method runs automatically when you call .save() on an object.
    # Here we customize it to auto-generate a QR code image each time a new session is created.
    def save(self, *args, **kwargs):
        # Generate the QR code only if it hasn’t been created yet
        if not self.qr_code:
            # The text (payload) encoded inside the QR — contains session and teacher info
            payload = f"session:{self.subject.id}:{self.teacher.id}:{self.date}"

            # Generate the actual QR image using qrcode library
            qr_img = qrcode.make(payload)

            # Store the image temporarily in memory
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            buffer.seek(0)

            # Give the file a name (like "Math_2025-11-13.png")
            filename = f"{self.subject.name}_{self.date}.png"

            # Save the image into Django’s media folder (without re-saving the model yet)
            self.qr_code.save(filename, File(buffer), save=False)

        # Finally, save the model normally (into the database)
        super().save(*args, **kwargs)


# ------------------------------------------------------------
# 🧩 AttendanceRecord Model
# ------------------------------------------------------------
# This table stores attendance information for each student per session
class AttendanceRecord(models.Model):
    # Link the record to a specific student (User table)
    student = models.ForeignKey(User, on_delete=models.CASCADE)

    # Link the record to the QR session (Math class 2025-11-13)
    session = models.ForeignKey(QRSession, on_delete=models.CASCADE)

    # Attendance status: Present / Absent / Late etc.
    status = models.CharField(max_length=20, default='Present')

    # Automatically record the timestamp when attendance was taken
    recorded_at = models.DateTimeField(auto_now_add=True)

    # Make sure each student can only have one record per session
    class Meta:
        unique_together = ('student', 'session')

    # Readable display in admin
    def __str__(self):
        return f"{self.student.username} - {self.session}"
