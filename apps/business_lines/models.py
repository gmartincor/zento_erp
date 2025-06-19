from django.db import models
from django.utils.text import slugify
from apps.core.models import TimeStampedModel


class BusinessLine(TimeStampedModel):
    """
    Hierarchical business line model with up to 3 levels.
    """
    
    class RemanenteChoices(models.TextChoices):
        REMANENTE_PEPE = 'remanente_pepe', 'Remanente Pepe'
        REMANENTE_PEPE_VIDEO = 'remanente_pepe_video', 'Remanente Pepe Video'
        REMANENTE_DANI = 'remanente_dani', 'Remanente Dani'
        REMANENTE_AVEN = 'remanente_aven', 'Remanente Aven'
    
    name = models.CharField(
        max_length=255,
        verbose_name="Nombre"
    )
    
    slug = models.SlugField(
        max_length=255,
        verbose_name="Slug"
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Línea padre",
        db_index=True
    )
    
    level = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Nivel",
        help_text="Nivel jerárquico (1-3)"
    )
    
    has_remanente = models.BooleanField(
        default=False,
        verbose_name="Tiene remanente"
    )
    
    remanente_field = models.CharField(
        max_length=30,
        choices=RemanenteChoices.choices,
        null=True,
        blank=True,
        verbose_name="Campo de remanente"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
        db_index=True
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden"
    )

    class Meta:
        db_table = 'business_lines'
        verbose_name = "Línea de negocio"
        verbose_name_plural = "Líneas de negocio"
        unique_together = [['name', 'parent']]
        ordering = ['level', 'order', 'name']
        indexes = [
            models.Index(fields=['parent', 'level']),
            models.Index(fields=['is_active', 'level']),
            models.Index(fields=['slug']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(level__gte=1) & models.Q(level__lte=3),
                name='business_line_level_range'
            ),
            models.CheckConstraint(
                check=models.Q(has_remanente=False) | models.Q(remanente_field__isnull=False),
                name='business_line_remanente_field_required'
            ),
        ]

    def save(self, *args, **kwargs):
        """
        Auto-calculate level based on parent hierarchy and generate slug.
        """
        # Auto-generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Auto-calculate level based on parent
        if self.parent is None:
            self.level = 1
        else:
            self.level = self.parent.level + 1
        
        # Validate maximum level
        if self.level > 3:
            raise ValueError("El nivel máximo permitido es 3")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{'  ' * (self.level - 1)}{self.name}"

    def get_full_hierarchy(self):
        """
        Returns the full hierarchy path as a string.
        """
        if self.parent:
            return f"{self.parent.get_full_hierarchy()} > {self.name}"
        return self.name

    def get_descendants(self):
        """
        Returns all descendants of this business line.
        """
        return BusinessLine.objects.select_related('parent').filter(
            parent__in=self.get_descendants_ids()
        )

    def get_descendants_ids(self):
        """
        Returns a list of all descendant IDs.
        """
        descendants = list(self.children.values_list('id', flat=True))
        for child in self.children.select_related('parent').all():
            descendants.extend(child.get_descendants_ids())
        return descendants

    def get_url_path(self):
        """
        Returns the hierarchical URL path for this business line.
        Example: 'jaen/pepe/pepe-normal'
        """
        path_parts = []
        current = self
        
        while current:
            path_parts.insert(0, current.slug)
            current = current.parent
        
        return '/'.join(path_parts)
