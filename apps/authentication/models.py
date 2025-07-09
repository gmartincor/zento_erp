from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    tenant = models.OneToOneField(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user',
        verbose_name="Tenant asociado"
    )

    class Meta:
        db_table = 'users'
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.username
