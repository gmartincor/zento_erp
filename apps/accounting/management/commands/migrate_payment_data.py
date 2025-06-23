from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from decimal import Decimal

from apps.accounting.models import ClientService, ServicePayment


class Command(BaseCommand):
    help = 'Migra datos del modelo ClientService al nuevo esquema con ServicePayment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecuta en modo dry-run sin hacer cambios reales',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Ejecutando en modo DRY-RUN - No se realizarán cambios')
            )

        migrated_count = 0
        error_count = 0

        # Obtener la migración anterior para recuperar datos
        from django.db import connection
        cursor = connection.cursor()
        
        # Verificar si existen las columnas antiguas
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='client_services' 
            AND column_name IN ('price', 'payment_method', 'start_date', 'renewal_date')
        """)
        
        old_columns = [row[0] for row in cursor.fetchall()]
        
        if not old_columns:
            self.stdout.write(
                self.style.WARNING(
                    'No se encontraron columnas antiguas. '
                    'Es posible que la migración de datos ya se haya ejecutado.'
                )
            )
            return

        # Recuperar datos de la migración anterior
        cursor.execute("""
            SELECT id, price, payment_method, start_date, renewal_date 
            FROM client_services 
            WHERE price IS NOT NULL AND start_date IS NOT NULL
        """)
        
        old_data = cursor.fetchall()
        
        self.stdout.write(f'Encontrados {len(old_data)} servicios para migrar')

        with transaction.atomic():
            if dry_run:
                transaction.set_rollback(True)

            for row in old_data:
                service_id, price, payment_method, start_date, renewal_date = row
                
                try:
                    client_service = ClientService.objects.get(id=service_id)
                    
                    # Crear el primer pago basado en los datos originales
                    period_start = start_date
                    
                    # Si hay fecha de renovación, usar esa como fin del primer período
                    if renewal_date:
                        period_end = renewal_date - timedelta(days=1)
                    else:
                        # Asumir un período de 1 mes por defecto
                        period_end = self._calculate_period_end(period_start, 1)

                    payment = ServicePayment(
                        client_service=client_service,
                        amount=Decimal(str(price)),
                        payment_date=start_date,
                        period_start=period_start,
                        period_end=period_end,
                        status=ServicePayment.StatusChoices.PAID,
                        payment_method=payment_method or 'CASH',
                        notes='Migrado desde datos originales'
                    )
                    
                    if not dry_run:
                        payment.save()
                    
                    migrated_count += 1
                    
                    if migrated_count % 50 == 0:
                        self.stdout.write(f'Migrados {migrated_count} servicios...')

                except ClientService.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'ClientService con ID {service_id} no encontrado')
                    )
                    error_count += 1
                    continue
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error migrando servicio {service_id}: {str(e)}'
                        )
                    )
                    error_count += 1
                    continue

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY-RUN completado: {migrated_count} servicios serían migrados, '
                    f'{error_count} errores encontrados'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Migración completada: {migrated_count} servicios migrados, '
                    f'{error_count} errores'
                )
            )

    def _calculate_period_end(self, start_date: date, duration_months: int) -> date:
        year = start_date.year
        month = start_date.month + duration_months
        
        while month > 12:
            month -= 12
            year += 1
        
        try:
            period_end = date(year, month, start_date.day) - timedelta(days=1)
        except ValueError:
            # Manejar casos como 31 de enero + 1 mes
            period_end = date(year, month, 1) - timedelta(days=1)
        
        return period_end
