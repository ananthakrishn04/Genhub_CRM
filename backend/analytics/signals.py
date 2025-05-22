from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Certificate


@receiver(pre_save, sender=Certificate)
def update_certificate_status(sender, instance, **kwargs):
    """Update certificate status before saving"""
    if instance.expiry_date:
        instance.update_status()


@receiver(post_save, sender=Certificate)
def schedule_certificate_reminder(sender, instance, created, **kwargs):
    """Schedule reminder for new certificates"""
    if created and instance.expiry_date:
        from .tasks import send_certificate_reminders
        # Check if reminder should be sent soon
        days_until_expiry = instance.days_until_expiry
        if 0 <= days_until_expiry <= instance.reminder_days_before:
            send_certificate_reminders.delay(instance.reminder_days_before)