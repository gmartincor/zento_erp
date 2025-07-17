"""
Comando de gestión para crear tenants en zentoerp.com
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.tenants.models import Tenant, Domain


class Command(BaseCommand):
    help = 'Crea un nuevo tenant con su dominio'

    def add_arguments(self, parser):
        parser.add_argument(
            'schema_name',
            type=str,
            help='Nombre del schema del tenant (ej: nutricion, consultorio)'
        )
        parser.add_argument(
            'domain_name',
            type=str,
            help='Nombre del dominio (ej: nutricion.zentoerp.com)'
        )
        parser.add_argument(
            'tenant_name',
            type=str,
            help='Nombre del tenant (ej: Nutrición Pro)'
        )
        parser.add_argument(
            '--description',
            type=str,
            default='',
            help='Descripción del tenant'
        )

    def handle(self, *args, **options):
        schema_name = options['schema_name']
        domain_name = options['domain_name']
        tenant_name = options['tenant_name']
        description = options['description']

        try:
            with transaction.atomic():
                # Crear tenant
                tenant = Tenant.objects.create(
                    schema_name=schema_name,
                    name=tenant_name,
                    description=description,
                    status=Tenant.StatusChoices.ACTIVE
                )

                # Crear dominio
                domain = Domain.objects.create(
                    domain=domain_name,
                    tenant=tenant,
                    is_primary=True
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Tenant "{tenant_name}" creado exitosamente\n'
                        f'   - Schema: {schema_name}\n'
                        f'   - Dominio: {domain_name}\n'
                        f'   - Estado: {tenant.status}\n'
                        f'   - Accesible en: https://{domain_name}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear tenant: {str(e)}')
            )
