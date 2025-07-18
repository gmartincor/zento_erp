from django.db import migrations

def migrate_entity_type_to_legal_form(apps, schema_editor):
    """Migra datos de entity_type a legal_form"""
    Company = apps.get_model('invoicing', 'Company')
    
    for company in Company.objects.all():
        if hasattr(company, 'entity_type'):
            if company.entity_type == 'FREELANCER':
                company.legal_form = 'AUTONOMO'
            elif company.entity_type == 'COMPANY':
                # Si no tiene legal_form definido, asumimos SL por defecto
                if not company.legal_form:
                    company.legal_form = 'SL'
            company.save()

def reverse_migration(apps, schema_editor):
    """Reversa la migración"""
    Company = apps.get_model('invoicing', 'Company')
    
    for company in Company.objects.all():
        if company.legal_form == 'AUTONOMO':
            company.entity_type = 'FREELANCER'
        else:
            company.entity_type = 'COMPANY'
        company.save()

class Migration(migrations.Migration):

    dependencies = [
        ('invoicing', '0006_update_entity_type_labels'),
    ]

    operations = [
        migrations.RunPython(migrate_entity_type_to_legal_form, reverse_migration),
    ]
