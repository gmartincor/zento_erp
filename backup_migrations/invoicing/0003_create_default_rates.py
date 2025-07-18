from django.db import migrations


def create_default_rates(apps, schema_editor):
    VATRate = apps.get_model('invoicing', 'VATRate')
    IRPFRate = apps.get_model('invoicing', 'IRPFRate')
    
    # Create VAT rates
    vat_rates = [
        {'name': 'General', 'rate': 21.0, 'is_default': True},
        {'name': 'Reducido', 'rate': 10.0, 'is_default': False},
        {'name': 'Super Reducido', 'rate': 4.0, 'is_default': False},
        {'name': 'Exento', 'rate': 0.0, 'is_default': False},
    ]
    
    for vat_data in vat_rates:
        VATRate.objects.create(**vat_data)
    
    # Create IRPF rates
    irpf_rates = [
        {'name': 'General', 'rate': 15.0, 'is_default': True},
        {'name': 'Profesional', 'rate': 7.0, 'is_default': False},
        {'name': 'Sin retención', 'rate': 0.0, 'is_default': False},
    ]
    
    for irpf_data in irpf_rates:
        IRPFRate.objects.create(**irpf_data)


def remove_default_rates(apps, schema_editor):
    VATRate = apps.get_model('invoicing', 'VATRate')
    IRPFRate = apps.get_model('invoicing', 'IRPFRate')
    
    VATRate.objects.all().delete()
    IRPFRate.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('invoicing', '0002_irpfrate_vatrate_remove_invoice_irpf_amount_and_more'),
    ]

    operations = [
        migrations.RunPython(create_default_rates, remove_default_rates),
    ]
