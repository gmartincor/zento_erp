from django.core.management.base import BaseCommand
from django.db import transaction
from apps.tenants.models import Tenant, Domain
from apps.core.constants import TENANT_SUCCESS_MESSAGES


class Command(BaseCommand):
    help = 'Configura el tenant principal para datos existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            default='Administrador Principal',
            help='Nombre del tenant principal'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@nutricionpro.com',
            help='Email del tenant principal'
        )
        parser.add_argument(
            '--schema-name',
            type=str,
            default='admin',
            help='Nombre del esquema del tenant principal'
        )
        parser.add_argument(
            '--domain',
            type=str,
            default='admin.localhost:8000',
            help='Dominio del tenant principal'
        )

    def handle(self, *args, **options):
        name = options['name']
        email = options['email']
        schema_name = options['schema_name']
        domain_name = options['domain']

        try:
            with transaction.atomic():
                if Tenant.objects.filter(schema_name=schema_name).exists():
                    self.stdout.write(
                        self.style.WARNING(f"Ya existe un tenant con el esquema '{schema_name}'")
                    )
                    return

                tenant = Tenant.objects.create(
                    name=name,
                    email=email,
                    schema_name=schema_name
                )

                domain = Domain.objects.create(
                    domain=domain_name,
                    tenant=tenant,
                    is_primary=True
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        TENANT_SUCCESS_MESSAGES['TENANT_CREATED'].format(name=name)
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creando tenant: {str(e)}')
            )
