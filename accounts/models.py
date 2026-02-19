from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings




# class Profile(models.Model):
#     ROLE_CHOICES = (
#         ('admin', 'Admin'),
#         ('teacher', 'Teacher'),
#         ('student', 'Student'),
#     )

#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
#     phone = models.CharField(max_length=15, blank=True, null=True)
    
#     def __str__(self):
#         return f"{self.user.username} - {self.role}"

# # Auto-create profile when user is created
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance, role='student')

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     if hasattr(instance, 'profile'):
#         instance.profile.save()




# class StudentProfile(models.Model):
#     user = models.OneToOneField(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )

#     student_id = models.IntegerField(unique=True)
#     full_name = models.CharField(max_length=100)

    # def __str__(self):
    #     return f"{self.student_id} - {self.full_name}"
    
class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    # student-only fields (SAFE to be blank)
    student_id = models.IntegerField(null=True, blank=True, unique=True)
    full_name = models.CharField(max_length=100, blank=True)

    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()
 


