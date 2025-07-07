# Generated manually to fix slug constraints

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0008_complete_django_tenants_setup'),
    ]

    operations = [
        # Only alter the slug field length to match what we need
        migrations.AlterField(
            model_name='tenant',
            name='slug',
            field=models.CharField(
                db_index=True, 
                help_text='Identificador único para URLs (ej: maria-fernandez -> /maria-fernandez/)', 
                max_length=50, 
                unique=True, 
                verbose_name='Slug'
            ),
        ),
    ]
