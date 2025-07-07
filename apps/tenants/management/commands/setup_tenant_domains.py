from django.core.management.base import BaseCommand
from django.conf import settings
from apps.tenants.models import Tenant, Domain


class Command(BaseCommand):
    help = 'Crea dominios para tenants existentes que no tengan dominios configurados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--base-domain',
            type=str,
            help='Dominio base (ej: miapp.com para producción, localhost para desarrollo)'
        )
        parser.add_argument(
            '--port',
            type=str,
            help='Puerto para desarrollo (solo se usa si es localhost)'
        )

    def handle(self, *args, **options):
        # Detectar entorno automáticamente
        is_development = settings.DEBUG
        
        # Configurar dominio base
        if options['base_domain']:
            base_domain = options['base_domain']
        else:
            if is_development:
                base_domain = 'localhost'
                self.stdout.write(
                    self.style.SUCCESS('🔧 Entorno de desarrollo detectado')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ En producción debes especificar --base-domain')
                )
                self.stdout.write('Ejemplo: python manage.py setup_tenant_domains --base-domain miapp.com')
                return
        
        # Configurar puerto
        port = None
        if base_domain == 'localhost':
            port = options.get('port', '8000')
            self.stdout.write(
                self.style.SUCCESS(f'🌐 Usando puerto {port} para desarrollo')
            )
        
        # Obtener todos los tenants que no sean el público
        tenants = Tenant.objects.exclude(schema_name='public')
        
        created_domains = 0
        
        for tenant in tenants:
            # Verificar si ya tiene un dominio primario
            primary_domain = Domain.objects.filter(tenant=tenant, is_primary=True).first()
            
            if not primary_domain:
                # Crear subdominio
                if is_development and base_domain == 'localhost':
                    subdomain = f"{tenant.schema_name}.{base_domain}:{port}"
                else:
                    subdomain = f"{tenant.schema_name}.{base_domain}"
                
                # Verificar que no exista este dominio
                if not Domain.objects.filter(domain=subdomain).exists():
                    Domain.objects.create(
                        domain=subdomain,
                        tenant=tenant,
                        is_primary=True
                    )
                    created_domains += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Dominio creado: {subdomain} -> {tenant.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Dominio ya existe: {subdomain}')
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Tenant {tenant.name} ya tiene dominio: {primary_domain.domain}')
                )
        
        if created_domains > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 Se crearon {created_domains} dominios nuevos')
            )
            
            if not is_development:
                self.stdout.write(
                    self.style.WARNING('\n⚠️  IMPORTANTE PARA PRODUCCIÓN:')
                )
                self.stdout.write(
                    self.style.WARNING('1. Configura tu servidor web (Nginx/Apache) para manejar subdominios')
                )
                self.stdout.write(
                    self.style.WARNING('2. Configura DNS wildcard: *.tu-dominio.com')
                )
                self.stdout.write(
                    self.style.WARNING('3. Configura SSL para todos los subdominios')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Todos los tenants ya tienen dominios configurados')
            )
