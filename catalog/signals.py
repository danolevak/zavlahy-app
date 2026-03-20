from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Field
from .services import store_et0_for_field


@receiver(post_save, sender=Field)
def fetch_et0_after_field_create(sender, instance, created, **kwargs):
    if created and instance.latitude and instance.longitude:
        try:
            store_et0_for_field(instance.id, 14)
        except Exception as e:
            print(f"Chyba pri automatickom načítaní ET0 pre pole {instance.id}: {e}")