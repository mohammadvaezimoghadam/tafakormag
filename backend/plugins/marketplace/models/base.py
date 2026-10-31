from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract base model providing self-updating created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ آخرین بروزرسانی")

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    """
    Custom queryset providing batch soft-delete, restore, and hard-delete operations.
    """
    def active(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)

    def delete(self):
        """Batch soft delete"""
        return self.update(deleted_at=timezone.now())

    def hard_delete(self):
        """Permanent physical database delete"""
        return super().delete()

    def restore(self):
        """Batch restore soft-deleted rows"""
        return self.update(deleted_at=None)


class SoftDeleteManager(models.Manager):
    """
    Default manager that filters out soft-deleted records automatically.
    """
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager):
    """
    Manager providing raw access to all records including soft-deleted ones.
    """
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(models.Model):
    """
    Abstract base model for entities that require soft-deletion instead of physical deletion.
    Preserves historical referential integrity for orders and financial audits.
    """
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name="زمان حذف نرم")

    # Default manager hides soft-deleted items
    objects = SoftDeleteManager()
    # Explicit manager including soft-deleted items for admin or audit routines
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """
        Soft delete: Stamps deleted_at with current timestamp instead of SQL DELETE.
        """
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        """
        Permanent physical removal from the database.
        """
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """
        Restores a previously soft-deleted instance.
        """
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class MarketplaceBaseModel(TimeStampedModel, SoftDeleteModel):
    """
    Composite abstract base model containing both audit timestamps and soft deletion capabilities.
    """
    class Meta:
        abstract = True
