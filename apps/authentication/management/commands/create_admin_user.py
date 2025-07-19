from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant
import getpass


User = get_user_model()


class Command(BaseCommand):
    help = 'Crea un superusuario en el contexto adecuado para producción'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username del superusuario')
        parser.add_argument('--email', type=str, help='Email del superusuario')
        parser.add_argument('--tenant', type=str, help='Schema del tenant (opcional, default: public)')
        parser.add_argument('--interactive', action='store_true', help='Modo interactivo', default=True)

    def handle(self, *args, **options):
        tenant_schema = options.get('tenant', 'public')
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 Creando superusuario en schema: {tenant_schema}')
        )
        
        # Obtener el tenant
        try:
            if tenant_schema == 'public':
                # Para el schema público, usar el tenant público
                tenant = Tenant.objects.filter(schema_name='public').first()
            else:
                tenant = Tenant.objects.get(schema_name=tenant_schema)
                
            if not tenant:
                self.stdout.write(
                    self.style.ERROR(f'❌ No se encontró el tenant: {tenant_schema}')
                )
                return
                
        except Tenant.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ No se encontró el tenant: {tenant_schema}')
            )
            return
        
        # Cambiar al contexto del tenant
        with schema_context(tenant_schema):
            self.stdout.write(f'📍 Contexto cambiado a: {tenant_schema}')
            
            if options.get('interactive'):
                # Modo interactivo
                username = options.get('username') or input('Username: ')
                email = options.get('email') or input('Email: ')
                
                # Verificar si el usuario ya existe
                if User.objects.filter(username=username).exists():
                    self.stdout.write(
                        self.style.ERROR(f'❌ El usuario {username} ya existe en {tenant_schema}')
                    )
                    return
                
                password = getpass.getpass('Password: ')
                password_confirm = getpass.getpass('Password (confirm): ')
                
                if password != password_confirm:
                    self.stdout.write(
                        self.style.ERROR('❌ Las contraseñas no coinciden')
                    )
                    return
                
                # Crear el superusuario
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                
                # SIEMPRE asociar al tenant (tanto public como otros)
                if tenant:
                    user.tenant = tenant
                    user.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Superusuario {username} creado exitosamente')
                )
                self.stdout.write(f'   📧 Email: {email}')
                self.stdout.write(f'   🏥 Tenant: {tenant.name if tenant else "Sin tenant"}')
                self.stdout.write(f'   📍 Schema: {tenant_schema}')
                
                if tenant_schema == 'principal':
                    self.stdout.write(f'   🌐 Acceso: https://zentoerp.com/')
                elif tenant_schema == 'public':
                    self.stdout.write(f'   🌐 Acceso: https://zentoerp-web.onrender.com/')
                
            else:
                # Usar el comando estándar de Django
                call_command('createsuperuser')
