from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract model that provides self-updating created and modified fields.
    """
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    modified = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        abstract = True
        ordering = ['-created']


class SoftDeleteModel(models.Model):
    """
    Abstract model that provides soft delete functionality.
    """
    is_deleted = models.BooleanField(default=False, verbose_name="Eliminado")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de eliminación")

    class Meta:
        abstract = True

    def soft_delete(self):
        """
        Marks the object as deleted instead of actually deleting it.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """
        Restores a soft deleted object.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])
