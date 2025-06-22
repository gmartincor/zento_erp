from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    modified = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        abstract = True
        ordering = ['-created']


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, verbose_name="Eliminado")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de eliminación")

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])
