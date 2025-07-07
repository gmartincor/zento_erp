from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    
    class RoleChoices(models.TextChoices):
        AUTONOMO = 'AUTONOMO', 'Autónomo'
    
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.AUTONOMO,
        verbose_name="Rol"
    )
    
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
        return f"{self.username} ({self.get_role_display()})"
