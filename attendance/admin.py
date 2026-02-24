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


# from django.contrib import admin
# from .models import Subject, QRSession, AttendanceRecord,StudentProfile,FeeStructure, Payment,Notification

# from .models import StudentProfile, FeeStructure, Payment

# admin.site.register(Subject)
# admin.site.register(QRSession)
# admin.site.register(AttendanceRecord)
# admin.site.register(StudentProfile)
# admin.site.register(FeeStructure)
# admin.site.register(Payment)
# admin.site.register(Notification)

# from django.contrib import admin
# from .models import StudentProfile, FeeStructure, Payment

# @admin.register(StudentProfile)
# class StudentProfileAdmin(admin.ModelAdmin):
#     list_display = ("student_id", "full_name", "user")
#     search_fields = ("full_name", "student_id", "user__username")

# @admin.register(FeeStructure)
# class FeeStructureAdmin(admin.ModelAdmin):
#     list_display = ("student", "semester", "total_fee", "due_date")
#     list_filter = ("semester",)
#     search_fields = ("student__full_name", "student__student_id")

# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = ("student", "semester", "amount", "paid_at", "note")
#     list_filter = ("semester",)
#     search_fields = ("student__full_name", "student__student_id", "note")


from django.contrib import admin
from .models import StudentProfile, FeeStructure, Payment, Notification, Subject, QRSession, AttendanceRecord

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("student_id", "full_name", "user")
    search_fields = ("student_id", "full_name", "user__username")
    list_select_related = ("user",)

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ("student", "semester", "total_fee", "due_date")
    list_filter = ("semester",)
    search_fields = ("student__full_name", "student__student_id")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("student", "semester", "amount", "paid_at", "note")
    list_filter = ("semester", "paid_at")
    search_fields = ("student__full_name", "student__student_id", "note")

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("student", "title", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("student__student_id", "student__full_name", "title")


admin.site.register(Subject)
admin.site.register(QRSession)
admin.site.register(AttendanceRecord)