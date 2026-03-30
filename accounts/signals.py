from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        role = "admin" if (instance.is_staff or instance.is_superuser) else "student"
        Profile.objects.get_or_create(
            user=instance,
            defaults={"role": role}
        )

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    Profile.objects.get_or_create(
        user=instance,
        defaults={
            "role": "admin" if (instance.is_staff or instance.is_superuser) else "student"
        }
    )

@receiver(user_logged_in)
def set_role_after_google_login(sender, request, user, **kwargs):
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={"role": "student"}
    )

    desired_role = request.session.pop("desired_role", None)

    if desired_role:
        profile.role = desired_role
        profile.save()
    elif not profile.role:
        profile.role = "student"
        profile.save()