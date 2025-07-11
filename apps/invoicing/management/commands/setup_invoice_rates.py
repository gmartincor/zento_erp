from django.core.management.base import BaseCommand
from django.db import transaction
from apps.invoicing.models import VATRate, IRPFRate
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sets up default VAT and IRPF rates for invoicing'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.setup_vat_rates()
            self.setup_irpf_rates()
        
        self.stdout.write(self.style.SUCCESS('Successfully set up default invoice rates'))
    
    def setup_vat_rates(self):
        # Clear any existing default status
        VATRate.objects.filter(is_default=True).update(is_default=False)
        
        vat_rates = [
            {'name': 'General', 'rate': 21.0, 'is_default': True},
            {'name': 'Reducido', 'rate': 10.0, 'is_default': False},
            {'name': 'Super Reducido', 'rate': 4.0, 'is_default': False},
            {'name': 'Exento', 'rate': 0.0, 'is_default': False},
        ]
        
        created_count = 0
        updated_count = 0
        
        for vat_data in vat_rates:
            rate_obj, created = VATRate.objects.update_or_create(
                name=vat_data['name'],
                defaults={'rate': vat_data['rate'], 'is_default': vat_data['is_default']}
            )
            
            if created:
                created_count += 1
                logger.info(f"Created VAT rate: {rate_obj.name} ({rate_obj.rate}%)")
            else:
                updated_count += 1
                logger.info(f"Updated VAT rate: {rate_obj.name} ({rate_obj.rate}%)")
        
        self.stdout.write(f"VAT rates: {created_count} created, {updated_count} updated")
    
    def setup_irpf_rates(self):
        # Clear any existing default status
        IRPFRate.objects.filter(is_default=True).update(is_default=False)
        
        irpf_rates = [
            {'name': 'General', 'rate': 15.0, 'is_default': True},
            {'name': 'Profesional', 'rate': 7.0, 'is_default': False},
            {'name': 'Sin retención', 'rate': 0.0, 'is_default': False},
        ]
        
        created_count = 0
        updated_count = 0
        
        for irpf_data in irpf_rates:
            rate_obj, created = IRPFRate.objects.update_or_create(
                name=irpf_data['name'],
                defaults={'rate': irpf_data['rate'], 'is_default': irpf_data['is_default']}
            )
            
            if created:
                created_count += 1
                logger.info(f"Created IRPF rate: {rate_obj.name} ({rate_obj.rate}%)")
            else:
                updated_count += 1
                logger.info(f"Updated IRPF rate: {rate_obj.name} ({rate_obj.rate}%)")
        
        self.stdout.write(f"IRPF rates: {created_count} created, {updated_count} updated")
