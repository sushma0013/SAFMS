from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import Profile
from .models import StudentProfile

@receiver(post_save, sender=Profile)
def create_student_profile(sender, instance, created, **kwargs):
    if instance.role == "student":
        StudentProfile.objects.get_or_create(
            user=instance.user,
            defaults={
                "student_id": f"STD-{instance.user.id}",
                "full_name": instance.user.get_full_name() or instance.user.username,
            }
        )