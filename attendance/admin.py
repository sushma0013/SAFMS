

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
    ClassSchedule,
)

from accounts.models import Profile
from django import forms
from django.forms import TimeInput


# =========================
# MAIN ADMIN SITE
# =========================
# class MainAdminSite(AdminSite):
#     site_header = "SAFMS Main Admin"
#     site_title = "Main Admin Portal"
#     index_title = "Attendance and System Management"

#     def has_permission(self, request):
#         return request.user.is_active and request.user.is_superuser
    
class MainAdminSite(AdminSite):
    site_header = "SAFMS Main Admin"
    site_title = "Main Admin Portal"
    index_title = "Attendance and System Management"

    def has_permission(self, request):
        return (
            request.user.is_active and (
                request.user.is_superuser or
                request.user.groups.filter(name="attendanceadmin").exists()
            )
        )   


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
    
class ClassScheduleForm(forms.ModelForm):
    class Meta:
        model = ClassSchedule
        fields = "__all__"
        widgets = {
            "start_time": TimeInput(format="%H:%M", attrs={"type": "time", "step": 60}),
            "end_time": TimeInput(format="%H:%M", attrs={"type": "time", "step": 60}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_time"].input_formats = ["%H:%M"]
        self.fields["end_time"].input_formats = ["%H:%M"]   

class ClassScheduleAdmin(admin.ModelAdmin):
    form = ClassScheduleForm
    list_display = ("subject", "teacher", "day_of_week", "start_time", "end_time", "room_name", "semester", "is_active")
    list_filter = ("day_of_week", "is_active", "semester")
    search_fields = ("subject__code", "subject__name", "teacher__username", "room_name")

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
main_admin_site.register(ClassSchedule, ClassScheduleAdmin)
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