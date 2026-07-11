import os
import logging
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Post, Topic

logger = logging.getLogger(__name__)

@receiver(post_delete, sender=Post)
def auto_delete_file_on_post_delete(sender, instance, **kwargs):
    """
    حذف فایل فیزیکی از روی دیسک پس از حذف رکورد پست
    """
    if instance.media_file:
        if os.path.isfile(instance.media_file.path):
            try:
                os.remove(instance.media_file.path)
                logger.info(f"Successfully deleted physical file for Post {instance.id} at {instance.media_file.path}")
            except Exception as e:
                logger.error(f"Error deleting physical file for Post {instance.id}: {str(e)}")

@receiver(post_delete, sender=Topic)
def auto_delete_file_on_topic_delete(sender, instance, **kwargs):
    """
    حذف تصویر فیزیکی تاپیک پس از حذف رکورد آن
    """
    if instance.image:
        if os.path.isfile(instance.image.path):
            try:
                os.remove(instance.image.path)
                logger.info(f"Successfully deleted physical image for Topic {instance.id} at {instance.image.path}")
            except Exception as e:
                logger.error(f"Error deleting physical image for Topic {instance.id}: {str(e)}")

@receiver(pre_save, sender=Post)
def auto_delete_file_on_post_change(sender, instance, **kwargs):
    """
    حذف فایل قدیمی در صورتی که فایل جدیدی برای پست آپلود شود یا فایل قبلی پاک شود
    """
    if not instance.pk:
        return False

    try:
        old_file = Post.objects.get(pk=instance.pk).media_file
    except Post.DoesNotExist:
        return False

    new_file = instance.media_file
    if not old_file:
        return False
        
    if not new_file or old_file.path != new_file.path:
        if os.path.isfile(old_file.path):
            try:
                os.remove(old_file.path)
                logger.info(f"Successfully deleted old physical file for Post {instance.id} on update")
            except Exception as e:
                logger.error(f"Error deleting old physical file on Post {instance.id} update: {str(e)}")

@receiver(pre_save, sender=Topic)
def auto_delete_file_on_topic_change(sender, instance, **kwargs):
    """
    حذف تصویر قدیمی تاپیک در صورتی که تصویر جدیدی جایگزین شود یا حذف گردد
    """
    if not instance.pk:
        return False

    try:
        old_image = Topic.objects.get(pk=instance.pk).image
    except Topic.DoesNotExist:
        return False

    new_image = instance.image
    if not old_image:
        return False
        
    if not new_image or old_image.path != new_image.path:
        if os.path.isfile(old_image.path):
            try:
                os.remove(old_image.path)
                logger.info(f"Successfully deleted old physical image for Topic {instance.id} on update")
            except Exception as e:
                logger.error(f"Error deleting old physical image on Topic {instance.id} update: {str(e)}")
