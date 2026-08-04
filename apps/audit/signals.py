from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.workflow.models import Movement
from .models import AuditLog

@receiver(post_save, sender=Movement)
def log_movement(sender, instance, created, **kwargs):
    if not created: return
    AuditLog.objects.create(
        actor=instance.from_user, action=instance.action,
        entity_type="Letter", entity_id=str(instance.letter_id),
        metadata={"to_user_id": instance.to_user_id, "comment": instance.comment},
    )
