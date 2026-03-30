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


# from django.contrib import admin
# from .models import StudentProfile, FeeStructure, Payment, Notification, Subject, QRSession, AttendanceRecord

# @admin.register(StudentProfile)
# class StudentProfileAdmin(admin.ModelAdmin):
#     list_display = ("student_id", "full_name", "user")
#     search_fields = ("student_id", "full_name", "user__username")
#     list_select_related = ("user",)

# @admin.register(FeeStructure)
# class FeeStructureAdmin(admin.ModelAdmin):
#     list_display = ("student", "semester", "total_fee", "due_date")
#     list_filter = ("semester",)
#     search_fields = ("student__full_name", "student__student_id")

# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = ("student", "semester", "amount", "paid_at", "note")
#     list_filter = ("semester", "paid_at")
#     search_fields = ("student__full_name", "student__student_id", "note")

# @admin.register(Notification)
# class NotificationAdmin(admin.ModelAdmin):
#     list_display = ("student", "title", "is_read", "created_at")
#     list_filter = ("is_read", "created_at")
#     search_fields = ("student__student_id", "student__full_name", "title")


# admin.site.register(Subject)
# admin.site.register(QRSession)
# admin.site.register(AttendanceRecord)

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

from django.contrib.admin import AdminSite
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

from .models import (
    StudentProfile,
    FeeStructure,
    Payment,
    Notification,
    PaymentRequest,
    KhaltiPayment,
    Subject,
    QRSession,
    AttendanceRecord,
)

from accounts.models import Profile


# =========================
# MAIN ADMIN SITE
# =========================
class MainAdminSite(AdminSite):
    site_header = "SAFMS Main Admin"
    site_title = "Main Admin Portal"
    index_title = "Attendance and System Management"

    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser
    
    


# =========================
# FEE ADMIN SITE
# =========================
class FeeAdminSite(AdminSite):
    site_header = "SAFMS Fee Admin"
    site_title = "Fee Admin Portal"
    index_title = "Fee Management"

    def has_permission(self, request):
        return (
            request.user.is_active and
            request.user.is_staff and
            request.user.groups.filter(name="feesmanager").exists()
        )


main_admin_site = MainAdminSite(name="main_admin")
fee_admin_site = FeeAdminSite(name="fee_admin")


# =========================
# MODEL ADMINS
# =========================
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("student_id", "full_name", "user")
    search_fields = ("student_id", "full_name", "user__username")
    list_select_related = ("user",)


class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ("student", "semester", "total_fee", "due_date")
    list_filter = ("semester",)
    search_fields = ("student__full_name", "student__student_id")


class PaymentAdmin(admin.ModelAdmin):
    list_display = ("student", "semester", "amount", "paid_at", "note")
    list_filter = ("semester", "paid_at")
    search_fields = ("student__full_name", "student__student_id", "note")


class NotificationAdmin(admin.ModelAdmin):
    list_display = ("student", "title", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("student__student_id", "student__full_name", "title")


class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "phone"]
    list_filter = ["role"]
    search_fields = ["user__username"]

class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ("student", "semester", "amount", "status", "created_at", "reviewed_by")
    list_filter = ("status", "semester", "created_at")
    search_fields = ("student__full_name", "student__student_id", "note")


class KhaltiPaymentAdmin(admin.ModelAdmin):
    list_display = ("student", "semester", "amount", "purchase_order_id", "pidx", "status")
    list_filter = ("status", "semester")
    search_fields = ("student__full_name", "student__student_id", "purchase_order_id", "pidx")


# =========================
# REGISTER MAIN ADMIN ONLY
# =========================
main_admin_site.register(User, UserAdmin)
main_admin_site.register(Group, GroupAdmin)

main_admin_site.register(Profile, ProfileAdmin)
main_admin_site.register(StudentProfile, StudentProfileAdmin)
main_admin_site.register(Subject)
main_admin_site.register(QRSession)
main_admin_site.register(AttendanceRecord)
main_admin_site.register(Site)
main_admin_site.register(SocialApp)


# =========================
# REGISTER FEE ADMIN ONLY
# =========================
fee_admin_site.register(FeeStructure, FeeStructureAdmin)
fee_admin_site.register(Payment, PaymentAdmin)
fee_admin_site.register(Notification, NotificationAdmin)
fee_admin_site.register(PaymentRequest, PaymentRequestAdmin)
fee_admin_site.register(KhaltiPayment, KhaltiPaymentAdmin)