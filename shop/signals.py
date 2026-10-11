"""Keep storage tidy: delete a card's image files when they are replaced or the card is deleted.

Without this, every re-upload would leave an orphaned file behind in Google Drive.
"""
from django.db import transaction
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import Card

IMAGE_FIELDS = ('image', 'back_image')


def _delete_later(field_file):
    """Delete after the DB transaction commits, so a failed save never loses the file."""
    if field_file and field_file.name:
        storage, name = field_file.storage, field_file.name
        transaction.on_commit(lambda: storage.delete(name))


@receiver(pre_save, sender=Card)
def delete_replaced_images(sender, instance, **kwargs):
    if not instance.pk:
        return
    old = Card.objects.filter(pk=instance.pk).only(*IMAGE_FIELDS).first()
    if not old:
        return
    for field in IMAGE_FIELDS:
        old_file = getattr(old, field)
        new_file = getattr(instance, field)
        if old_file and old_file.name != (new_file.name if new_file else None):
            _delete_later(old_file)


@receiver(post_delete, sender=Card)
def delete_images_of_deleted_card(sender, instance, **kwargs):
    for field in IMAGE_FIELDS:
        _delete_later(getattr(instance, field))
