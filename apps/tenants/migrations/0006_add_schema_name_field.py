# Generated manually for django-tenants migration

from django.db import migrations, models
import django_tenants.postgresql_backend.base


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0005_replace_subdomain_with_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='schema_name',
            field=models.CharField(db_index=True, max_length=63, null=True, blank=True, validators=[django_tenants.postgresql_backend.base._check_schema_name]),
        ),
    ]
