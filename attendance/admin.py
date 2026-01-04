# from django.contrib import admin
# from .models import Subject, QRSession, AttendanceRecord

# @admin.register(Subject)
# class SubjectAdmin(admin.ModelAdmin):
#     list_display = ('code', 'name', 'teacher', 'semester', 'department')
#     search_fields = ('code', 'name', 'teacher__username')

# @admin.register(QRSession)
# class QRSessionAdmin(admin.ModelAdmin):
#     list_display = ('id', 'subject', 'created_by', 'session_date', 'created_at', 'valid_until', 'is_closed')
#     list_filter = ('session_date', 'is_closed', 'subject')
#     search_fields = ('subject__name', 'created_by__username')

# @admin.register(AttendanceRecord)
# class AttendanceRecordAdmin(admin.ModelAdmin):
#     list_display = ('id', 'student', 'subject', 'session', 'status', 'date', 'recorded_at')
#     list_filter = ('status', 'subject', 'date')
#     search_fields = ('student__username', 'subject__name')


from django.contrib import admin
from .models import Subject, QRSession, AttendanceRecord

admin.site.register(Subject)
admin.site.register(QRSession)
admin.site.register(AttendanceRecord)
