from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django_tenants.utils import schema_context
from datetime import date, timedelta
from decimal import Decimal
import random

from apps.tenants.models import Tenant
from apps.business_lines.models import BusinessLine
from apps.accounting.models import Client, ClientService, ServicePayment
from apps.expenses.models import ExpenseCategory, Expense
from apps.core.constants import SERVICE_CATEGORIES


class Command(BaseCommand):
    help = 'Puebla de datos de prueba el tenant de Sofia'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecuta en modo dry-run sin hacer cambios reales',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Ejecutando en modo DRY-RUN'))

        try:
            sofia_tenant = Tenant.objects.get(name__icontains='sofia')
        except Tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR('Tenant Sofia no encontrado'))
            return

        with schema_context(sofia_tenant.schema_name):
            if dry_run:
                self.stdout.write('Creando datos de prueba...')
                self._create_business_lines()
                self._create_expense_categories()
                self._create_clients()
                self._create_client_services()
                self._create_service_payments()
                self._create_expenses()
            else:
                with transaction.atomic():
                    self._create_business_lines()
                    self._create_expense_categories()
                    self._create_clients()
                    self._create_client_services()
                    self._create_service_payments()
                    self._create_expenses()

        status = 'DRY-RUN completado' if dry_run else 'Datos creados exitosamente'
        self.stdout.write(self.style.SUCCESS(f'{status} para tenant Sofia'))

    def _create_business_lines(self):
        if BusinessLine.objects.exists():
            self.stdout.write('Business lines ya existen, omitiendo...')
            return
            
        lines_data = [
            {'name': 'Consulta Presencial', 'level': 1, 'children': [
                {'name': 'Primera Consulta', 'level': 2},
                {'name': 'Seguimiento Mensual', 'level': 2},
                {'name': 'Plan Especial', 'level': 2}
            ]},
            {'name': 'Consulta Online', 'level': 1, 'children': [
                {'name': 'Videollamada Individual', 'level': 2},
                {'name': 'Plan Digital', 'level': 2}
            ]},
            {'name': 'Programas Especiales', 'level': 1, 'children': [
                {'name': 'Detox 21 días', 'level': 2},
                {'name': 'Programa Deportistas', 'level': 2}
            ]}
        ]
        
        for line_data in lines_data:
            parent = BusinessLine.objects.create(
                name=line_data['name'],
                level=line_data['level'],
                is_active=True,
                order=lines_data.index(line_data) + 1
            )
            
            for child_data in line_data['children']:
                BusinessLine.objects.create(
                    name=child_data['name'],
                    parent=parent,
                    level=child_data['level'],
                    is_active=True,
                    order=line_data['children'].index(child_data) + 1
                )

    def _create_expense_categories(self):
        if ExpenseCategory.objects.exists():
            self.stdout.write('Expense categories ya existen, omitiendo...')
            return
            
        categories_data = [
            {'name': 'Alquiler Consulta', 'category_type': 'FIXED'},
            {'name': 'Suministros', 'category_type': 'FIXED'},
            {'name': 'Material Consulta', 'category_type': 'VARIABLE'},
            {'name': 'Marketing Digital', 'category_type': 'VARIABLE'},
            {'name': 'Formación', 'category_type': 'OCCASIONAL'},
            {'name': 'IVA', 'category_type': 'TAX'},
        ]
        
        for cat_data in categories_data:
            ExpenseCategory.objects.create(**cat_data, is_active=True)

    def _create_clients(self):
        if Client.objects.exists():
            self.stdout.write('Clients ya existen, omitiendo...')
            return
            
        clients_data = [
            {'full_name': 'Ana López Martín', 'dni': '12345678A', 'gender': 'F', 'email': 'ana.lopez@email.com', 'phone': '+34 666 111 222'},
            {'full_name': 'Carlos Ruiz Gómez', 'dni': '87654321B', 'gender': 'M', 'email': 'carlos.ruiz@gmail.com', 'phone': '+34 677 333 444'},
            {'full_name': 'María García Silva', 'dni': '45612378C', 'gender': 'F', 'email': 'maria.garcia@outlook.com', 'phone': '+34 688 555 666'},
            {'full_name': 'Pedro Fernández', 'dni': '78912345D', 'gender': 'M', 'email': 'pedro.fernandez@email.com', 'phone': '+34 699 777 888'},
            {'full_name': 'Laura Martínez', 'dni': '32165498E', 'gender': 'F', 'email': 'laura.martinez@gmail.com', 'phone': '+34 655 999 000'},
            {'full_name': 'José Antonio Vega', 'dni': '65498732F', 'gender': 'M', 'email': 'jose.vega@yahoo.com', 'phone': '+34 644 222 333'}
        ]
        
        for client_data in clients_data:
            Client.objects.create(**client_data, is_active=True)

    def _create_client_services(self):
        clients = list(Client.objects.all())
        business_lines = list(BusinessLine.objects.filter(level=2))
        categories = [SERVICE_CATEGORIES['PERSONAL'], SERVICE_CATEGORIES['BUSINESS']]
        prices = [90, 120, 150, 180, 200, 250]
        admin_statuses = ['ENABLED', 'SUSPENDED']
        
        for client in clients:
            num_services = random.randint(1, 2)
            selected_lines = random.sample(business_lines, min(num_services, len(business_lines)))
            
            for business_line in selected_lines:
                category = random.choice(categories)
                price = random.choice(prices)
                admin_status = random.choices(admin_statuses, weights=[85, 15])[0]
                
                start_date = date.today() - timedelta(days=random.randint(30, 180))
                end_date = start_date + timedelta(days=random.randint(90, 365))
                
                remanentes = {}
                if category == SERVICE_CATEGORIES['BUSINESS']:
                    remanentes = {
                        f'remanente_{client.dni.lower()}': str(random.uniform(20, 100))
                    }
                
                ClientService.objects.create(
                    client=client,
                    business_line=business_line,
                    category=category,
                    price=Decimal(str(price)),
                    start_date=start_date,
                    end_date=end_date,
                    admin_status=admin_status,
                    remanentes=remanentes,
                    is_active=admin_status == 'ENABLED'
                )

    def _create_service_payments(self):
        services = ClientService.objects.all()
        payment_methods = ['CARD', 'CASH', 'TRANSFER', 'BIZUM', 'PAYPAL']
        statuses = ['PAID', 'UNPAID_ACTIVE', 'OVERDUE', 'REFUNDED']
        status_weights = [60, 25, 10, 5]
        
        for service in services:
            if not service.is_active:
                continue
                
            num_payments = random.randint(1, 4)
            start_date = service.start_date
            
            for i in range(num_payments):
                period_start = start_date + timedelta(days=i * 30)
                period_end = period_start + timedelta(days=29)
                
                if period_start > service.end_date:
                    break
                    
                status = random.choices(statuses, weights=status_weights)[0]
                payment_method = random.choice(payment_methods)
                
                amount = service.price
                payment_date = None
                refunded_amount = Decimal('0')
                
                if status == 'PAID':
                    payment_date = period_start + timedelta(days=random.randint(0, 10))
                elif status == 'REFUNDED':
                    payment_date = period_start + timedelta(days=random.randint(0, 10))
                    refunded_amount = amount * Decimal(str(random.uniform(0.5, 1.0)))
                
                remanente = None
                if service.category == SERVICE_CATEGORIES['BUSINESS'] and random.choice([True, False]):
                    remanente = Decimal(str(random.uniform(-50, 50)))
                
                ServicePayment.objects.create(
                    client_service=service,
                    amount=amount,
                    payment_date=payment_date,
                    period_start=period_start,
                    period_end=period_end,
                    status=status,
                    payment_method=payment_method if payment_date else None,
                    remanente=remanente,
                    refunded_amount=refunded_amount,
                    notes=f'Pago período {i+1}' if status == 'PAID' else ''
                )

    def _create_expenses(self):
        categories = list(ExpenseCategory.objects.all())
        current_year = date.today().year
        
        for month in range(1, 8):
            for category in categories:
                if category.category_type == 'FIXED':
                    amount = random.uniform(300, 800)
                    description = f'{category.name} - {month:02d}/{current_year}'
                elif category.category_type == 'VARIABLE':
                    amount = random.uniform(50, 300)
                    description = f'{category.name} - Mes {month}'
                elif category.category_type == 'OCCASIONAL':
                    if random.choice([True, False, False]):
                        amount = random.uniform(100, 500)
                        description = f'{category.name} - Evento especial'
                    else:
                        continue
                else:
                    amount = random.uniform(200, 600)
                    description = f'{category.name} - Trimestre'
                
                expense_date = date(current_year, month, random.randint(1, 28))
                
                Expense.objects.create(
                    category=category,
                    amount=Decimal(str(round(amount, 2))),
                    date=expense_date,
                    description=description,
                    accounting_year=current_year,
                    accounting_month=month
                )
