from django.core.management.base import BaseCommand
from django.db import transaction
from apps.tenants.models import Tenant, Domain
from apps.core.constants import TENANT_SUCCESS_MESSAGES, TENANT_ERROR_MESSAGES


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
            '--subdomain',
            type=str,
            default='admin',
            help='Subdominio del tenant principal'
        )

    def handle(self, *args, **options):
        name = options['name']
        email = options['email']
        subdomain = options['subdomain']

        try:
            with transaction.atomic():
                if Tenant.objects.filter(subdomain=subdomain).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            TENANT_ERROR_MESSAGES['SUBDOMAIN_EXISTS'].format(subdomain=subdomain)
                        )
                    )
                    return

                tenant = Tenant.objects.create(
                    name=name,
                    email=email,
                    subdomain=subdomain
                )

                domain = Domain.objects.create(
                    domain=f'{subdomain}.localhost:8000',
                    tenant=tenant,
                    is_primary=True
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        TENANT_SUCCESS_MESSAGES['TENANT_CREATED'].format(name=name)
                    )
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Dominio: {domain.domain}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
