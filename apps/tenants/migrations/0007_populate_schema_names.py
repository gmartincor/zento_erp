# Generated manually for django-tenants data migration

from django.db import migrations


def populate_schema_names(apps, schema_editor):
    Tenant = apps.get_model('tenants', 'Tenant')
    for tenant in Tenant.objects.all():
        tenant.schema_name = tenant.slug.replace('-', '_')
        tenant.save()


def reverse_populate_schema_names(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0006_add_schema_name_field'),
    ]

    operations = [
        migrations.RunPython(populate_schema_names, reverse_populate_schema_names),
    ]
