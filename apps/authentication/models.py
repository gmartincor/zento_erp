from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with role-based access and business line relationships.
    """
    
    class RoleChoices(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        GLOW_VIEWER = 'GLOW_VIEWER', 'Visualizador Glow'
    
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.GLOW_VIEWER,
        verbose_name="Rol"
    )
    
    business_lines = models.ManyToManyField(
        'business_lines.BusinessLine',
        blank=True,
        verbose_name="Líneas de negocio",
        related_name="users"
    )

    class Meta:
        db_table = 'users'
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
