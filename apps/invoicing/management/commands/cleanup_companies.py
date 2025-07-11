from django.core.management.base import BaseCommand
from django.db import transaction
from django_tenants.utils import get_tenant_model, schema_context
from apps.invoicing.models import Company


class Command(BaseCommand):
    help = 'Limpia empresas duplicadas, manteniendo solo una por tenant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se haría sin hacer cambios',
        )
        parser.add_argument(
            '--tenant',
            type=str,
            help='Procesar solo un tenant específico',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        tenant_name = options.get('tenant')

        if dry_run:
            self.stdout.write(self.style.WARNING('Modo DRY-RUN activado'))

        TenantModel = get_tenant_model()
        tenants_qs = TenantModel.objects.exclude(schema_name='public')
        
        if tenant_name:
            tenants_qs = tenants_qs.filter(name__icontains=tenant_name)

        for tenant in tenants_qs:
            self.stdout.write(f'\nProcesando tenant: {tenant.name} ({tenant.schema_name})')
            
            with schema_context(tenant.schema_name):
                companies = Company.objects.all()
                company_count = companies.count()
                
                if company_count == 0:
                    self.stdout.write(f'  Sin empresas en {tenant.name}')
                elif company_count == 1:
                    self.stdout.write(f'  Una empresa encontrada en {tenant.name}: {companies.first().business_name}')
                else:
                    self.stdout.write(f'  {company_count} empresas encontradas en {tenant.name}')
                    
                    if not dry_run:
                        with transaction.atomic():
                            companies_to_keep = companies.first()
                            companies_to_delete = companies.exclude(pk=companies_to_keep.pk)
                            
                            for company in companies_to_delete:
                                self.stdout.write(f'    Eliminando: {company.business_name}')
                                company.delete()
                            
                            self.stdout.write(f'    Manteniendo: {companies_to_keep.business_name}')
                    else:
                        companies_to_keep = companies.first()
                        companies_to_delete = companies.exclude(pk=companies_to_keep.pk)
                        
                        for company in companies_to_delete:
                            self.stdout.write(f'    [DRY-RUN] Eliminaría: {company.business_name}')
                        
                        self.stdout.write(f'    [DRY-RUN] Mantendría: {companies_to_keep.business_name}')

        if dry_run:
            self.stdout.write(self.style.SUCCESS('\nDRY-RUN completado'))
        else:
            self.stdout.write(self.style.SUCCESS('\nLimpieza completada'))
