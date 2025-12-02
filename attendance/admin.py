# attendance/admin.py
from django.contrib import admin
from .models import Subject, QRSession, AttendanceRecord

admin.site.register(Subject)
admin.site.register(QRSession)
admin.site.register(AttendanceRecord)
# admin.site.register(QRSession)

