from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant, Domain
from apps.authentication.models import User
from django.contrib.auth.hashers import make_password
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Configura el tenant público para la aplicación'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            help='Dominio para el tenant público (ej: miapp.com o localhost para desarrollo)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar recreación del tenant público si ya existe'
        )

    def handle(self, *args, **options):
        # Detectar el entorno automáticamente
        is_development = settings.DEBUG
        
        if options['domain']:
            domain_name = options['domain']
        else:
            if is_development:
                domain_name = 'localhost:8000'
                self.stdout.write(
                    self.style.SUCCESS('🔧 Entorno de desarrollo detectado, usando localhost:8000')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ En producción debes especificar el dominio con --domain')
                )
                self.stdout.write('Ejemplo: python manage.py setup_public_tenant --domain miapp.com')
                return

        try:
            # Verificar si ya existe un tenant público
            public_tenant = Tenant.objects.filter(schema_name='public').first()
            
            if public_tenant and not options['force']:
                self.stdout.write(
                    self.style.WARNING(f'El tenant público ya existe: {public_tenant.name}')
                )
                
                # Verificar si existe el dominio
                domain_exists = Domain.objects.filter(
                    domain=domain_name, 
                    tenant=public_tenant
                ).exists()
                
                if not domain_exists:
                    Domain.objects.create(
                        domain=domain_name,
                        tenant=public_tenant,
                        is_primary=True
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Dominio {domain_name} agregado al tenant público')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ El dominio {domain_name} ya existe para el tenant público')
                    )
            else:
                if options['force'] and public_tenant:
                    self.stdout.write(
                        self.style.WARNING('🔄 Recreando tenant público...')
                    )
                    public_tenant.delete()
                
                # Crear tenant público
                public_tenant = Tenant.objects.create(
                    schema_name='public',
                    name='Portal Principal' if not is_development else 'Tenant Público (Desarrollo)',
                    email='admin@' + (domain_name.split(':')[0] if ':' in domain_name else domain_name),
                    status=Tenant.StatusChoices.ACTIVE,
                    is_active=True
                )
                
                # Crear dominio para el tenant público
                Domain.objects.create(
                    domain=domain_name,
                    tenant=public_tenant,
                    is_primary=True
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Tenant público creado con dominio: {domain_name}')
                )

            # Crear usuario administrador para el tenant público si no existe
            with schema_context('public'):
                admin_user = User.objects.filter(username='admin').first()
                
                if not admin_user:
                    admin_password = 'admin123' if is_development else self._generate_secure_password()
                    
                    admin_user = User.objects.create(
                        username='admin',
                        email='admin@' + (domain_name.split(':')[0] if ':' in domain_name else domain_name),
                        password=make_password(admin_password),
                        is_staff=True,
                        is_superuser=True,
                        is_active=True,
                        tenant=public_tenant
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS('✅ Usuario administrador creado para el tenant público')
                    )
                    
                    if is_development:
                        self.stdout.write(
                            self.style.WARNING('👤 Username: admin, Password: admin123')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'👤 Username: admin, Password: {admin_password}')
                        )
                        self.stdout.write(
                            self.style.ERROR('🔐 GUARDA ESTA CONTRASEÑA DE FORMA SEGURA')
                        )
                else:
                    # Asegurar que el admin esté asociado al tenant público
                    if admin_user.tenant != public_tenant:
                        admin_user.tenant = public_tenant
                        admin_user.save()
                        self.stdout.write(
                            self.style.SUCCESS('✅ Usuario administrador asociado al tenant público')
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS('✅ Usuario administrador ya existe para el tenant público')
                        )

            self.stdout.write(
                self.style.SUCCESS('\n🎉 Configuración del tenant público completada')
            )
            
            if is_development:
                self.stdout.write(
                    self.style.SUCCESS(f'🌐 Acceso: http://{domain_name}/')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'🌐 Acceso: https://{domain_name}/')
                )
                self.stdout.write(
                    self.style.WARNING('⚠️  Asegúrate de que tu servidor web esté configurado para servir subdominios')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al configurar el tenant público: {str(e)}')
            )
    
    def _generate_secure_password(self):
        """Genera una contraseña segura para producción"""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for i in range(16))
        return password
