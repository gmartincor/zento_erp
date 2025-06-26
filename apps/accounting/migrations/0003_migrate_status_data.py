from django.db import migrations


def migrate_status_to_admin_status(apps, schema_editor):
    ClientService = apps.get_model('accounting', 'ClientService')
    
    for service in ClientService.objects.all():
        if service.status in ['ACTIVE', 'EXPIRED']:
            service.admin_status = 'ENABLED'
        else:
            service.admin_status = 'DISABLED'
        service.save(update_fields=['admin_status'])


def reverse_migrate_admin_status_to_status(apps, schema_editor):
    ClientService = apps.get_model('accounting', 'ClientService')
    
    for service in ClientService.objects.all():
        if service.admin_status == 'ENABLED':
            service.status = 'ACTIVE'
        else:
            service.status = 'INACTIVE'
        service.save(update_fields=['status'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0002_refactor_service_status'),
    ]

    operations = [
        migrations.RunPython(
            migrate_status_to_admin_status,
            reverse_migrate_admin_status_to_status
        ),
    ]
