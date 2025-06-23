from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from decimal import Decimal
import random

from apps.accounting.models import ClientService, ServicePayment


class Command(BaseCommand):
    help = 'Crea datos de ejemplo para ServicePayment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--services',
            type=int,
            default=5,
            help='Número de servicios a los que agregar pagos de ejemplo',
        )

    def handle(self, *args, **options):
        services_count = options['services']
        
        # Obtener servicios activos
        services = ClientService.objects.filter(is_active=True)[:services_count]
        
        if not services:
            self.stdout.write(
                self.style.ERROR('No hay servicios activos para crear pagos de ejemplo')
            )
            return

        created_payments = 0
        
        with transaction.atomic():
            for service in services:
                # Crear 1-3 pagos históricos para cada servicio
                num_payments = random.randint(1, 3)
                
                start_date = date(2024, random.randint(1, 12), random.randint(1, 28))
                
                for i in range(num_payments):
                    # Calcular período
                    period_start = start_date + timedelta(days=i * 30)
                    period_end = period_start + timedelta(days=29)
                    
                    # Generar datos aleatorios realistas
                    amount = Decimal(random.choice([50, 75, 100, 125, 150, 200]))
                    payment_methods = ['CASH', 'CARD', 'TRANSFER', 'BIZUM']
                    payment_method = random.choice(payment_methods)
                    
                    # Crear el pago
                    payment = ServicePayment.objects.create(
                        client_service=service,
                        amount=amount,
                        payment_date=period_start,
                        period_start=period_start,
                        period_end=period_end,
                        status=ServicePayment.StatusChoices.PAID,
                        payment_method=payment_method,
                        notes=f'Pago de ejemplo #{i+1} para {service.client.full_name}'
                    )
                    
                    created_payments += 1
                    
                    self.stdout.write(f'Creado pago: {payment.amount}€ para {service.client.full_name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Se crearon {created_payments} pagos de ejemplo para {len(services)} servicios'
            )
        )
