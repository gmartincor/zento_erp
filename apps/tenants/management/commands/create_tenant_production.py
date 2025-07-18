from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_tenants.utils import get_tenant_model, get_tenant_domain_model
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Create a new tenant with production-compatible fields'

    def add_arguments(self, parser):
        parser.add_argument('--name', required=True, help='Tenant name')
        parser.add_argument('--email', required=True, help='Tenant email')
        parser.add_argument('--domain', required=True, help='Tenant domain')
        parser.add_argument('--schema', required=True, help='Schema name')
        parser.add_argument('--phone', default="", help='Phone number')
        parser.add_argument('--professional-number', default="", help='Professional number')
        parser.add_argument('--notes', default="", help='Additional notes')

    def handle(self, *args, **options):
        Tenant = get_tenant_model()
        Domain = get_tenant_domain_model()
        
        # Verificar si ya existe un tenant con este schema
        if Tenant.objects.filter(schema_name=options['schema']).exists():
            raise CommandError(f'Tenant with schema "{options["schema"]}" already exists')
        
        # Verificar si ya existe un tenant con este email
        if Tenant.objects.filter(email=options['email']).exists():
            raise CommandError(f'Tenant with email "{options["email"]}" already exists')

        try:
            with transaction.atomic():
                # Crear tenant con todos los campos requeridos
                tenant = Tenant.objects.create(
                    schema_name=options['schema'],
                    name=options['name'],
                    email=options['email'],
                    phone=options['phone'],
                    professional_number=options['professional_number'],
                    notes=options['notes'],
                    status=Tenant.StatusChoices.ACTIVE
                    # El slug se genera automáticamente en el método save()
                )
                
                # Crear dominio
                domain = Domain.objects.create(
                    domain=options['domain'],
                    tenant=tenant,
                    is_primary=True
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Successfully created tenant:\n'
                        f'   Name: {tenant.name}\n'
                        f'   Email: {tenant.email}\n'
                        f'   Schema: {tenant.schema_name}\n'
                        f'   Domain: {domain.domain}\n'
                        f'   Slug: {tenant.slug}\n'
                        f'   Status: {tenant.status}'
                    )
                )
                
        except Exception as e:
            raise CommandError(f'Error creating tenant: {e}')
