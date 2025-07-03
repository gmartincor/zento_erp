from django.core.management.base import BaseCommand
from django.db import transaction
from apps.accounting.models import ClientService, ServicePayment


class Command(BaseCommand):
    help = 'Actualiza el end_date de los servicios basado en sus últimos períodos (pagados o no)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se actualizaría sin hacer cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write("MODO DRY RUN - No se harán cambios reales")
        
        updated_count = 0
        
        with transaction.atomic():
            services = ClientService.objects.all()
            
            for service in services:
                latest_period = service.payments.filter(
                    status__in=[
                        ServicePayment.StatusChoices.PERIOD_CREATED,
                        ServicePayment.StatusChoices.PAID
                    ]
                ).order_by('-period_end').first()
                
                if latest_period:
                    new_end_date = latest_period.period_end
                    
                    if not service.end_date or service.end_date != new_end_date:
                        self.stdout.write(
                            f"Servicio {service.id} - {service.client.full_name}: "
                            f"{service.end_date} -> {new_end_date}"
                        )
                        
                        if not dry_run:
                            service.end_date = new_end_date
                            service.save(update_fields=['end_date'])
                        
                        updated_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'Se actualizarían {updated_count} servicios')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Se actualizaron {updated_count} servicios')
            )
