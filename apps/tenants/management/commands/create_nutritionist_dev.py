from django.core.management.base import BaseCommand
from django.conf import settings
from apps.tenants.models import Tenant, Domain
from apps.tenants.services import TenantCreationService
from apps.authentication.models import User
import re
import subprocess
import platform
import getpass


class Command(BaseCommand):
    help = 'Crea un nuevo nutricionista para desarrollo local de forma interactiva'

    def add_arguments(self, parser):
        parser.add_argument('--non-interactive', action='store_true', 
                          help='Modo no interactivo (usar con otros parámetros)')
        parser.add_argument('--name', type=str, help='Nombre del nutricionista')
        parser.add_argument('--username', type=str, help='Username para login')
        parser.add_argument('--password', type=str, help='Password para login')
        parser.add_argument('--email', type=str, help='Email del nutricionista')
        parser.add_argument('--domain', type=str, help='Dominio (ej: carlos.localhost)')
        parser.add_argument('--skip-hosts', action='store_true', 
                          help='No configurar /etc/hosts automáticamente')

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🏠 CREADOR DE NUTRICIONISTA - DESARROLLO LOCAL')
        )
        self.stdout.write('='*50)
        
        if options.get('non_interactive'):
            # Modo no interactivo - usar parámetros
            self._create_non_interactive(options)
        else:
            # Modo interactivo - preguntar datos
            self._create_interactive()

    def _create_interactive(self):
        """Modo interactivo para crear nutricionista"""
        try:
            self.stdout.write('')
            self.stdout.write('📋 Ingresa los datos del nutricionista:')
            self.stdout.write('')
            
            # Recopilar datos
            name = input('👤 Nombre completo: ').strip()
            if not name:
                self.stdout.write(self.style.ERROR('❌ El nombre es requerido'))
                return
            
            username = input('🔑 Username: ').strip()
            if not username:
                self.stdout.write(self.style.ERROR('❌ El username es requerido'))
                return
            
            email = input('📧 Email: ').strip()
            if not email:
                self.stdout.write(self.style.ERROR('❌ El email es requerido'))
                return
            
            # Sugerir dominio basado en username
            suggested_domain = f"{username.lower()}.localhost"
            domain_input = input(f'🌐 Dominio [{suggested_domain}]: ').strip()
            domain_name = domain_input if domain_input else suggested_domain
            
            # Password con confirmación
            password = getpass.getpass('🔐 Password: ')
            if not password:
                self.stdout.write(self.style.ERROR('❌ El password es requerido'))
                return
                
            password_confirm = getpass.getpass('🔐 Confirmar password: ')
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('❌ Las contraseñas no coinciden'))
                return
            
            # Confirmar datos
            self.stdout.write('')
            self.stdout.write('📋 RESUMEN DE DATOS:')
            self.stdout.write(f'   👤 Nombre: {name}')
            self.stdout.write(f'   🔑 Username: {username}')
            self.stdout.write(f'   📧 Email: {email}')
            self.stdout.write(f'   🌐 Dominio: {domain_name}')
            self.stdout.write('')
            
            confirm = input('¿Crear nutricionista? (s/N): ').strip().lower()
            if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
                self.stdout.write(self.style.WARNING('❌ Operación cancelada'))
                return
            
            # Crear nutricionista
            self._create_nutritionist(name, username, password, email, domain_name)
            
        except KeyboardInterrupt:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('❌ Operación cancelada por el usuario'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error inesperado: {str(e)}'))

    def _create_non_interactive(self, options):
        """Modo no interactivo usando parámetros"""
        required_fields = ['name', 'username', 'password', 'email', 'domain']
        missing_fields = [field for field in required_fields if not options.get(field)]
        
        if missing_fields:
            self.stdout.write(
                self.style.ERROR(f'❌ Faltan campos requeridos: {", ".join(missing_fields)}')
            )
            return
        
        self._create_nutritionist(
            options['name'],
            options['username'], 
            options['password'],
            options['email'],
            options['domain'],
            options.get('skip_hosts', False)
        )

    def _create_nutritionist(self, name, username, password, email, domain_name, skip_hosts=False):
        try:
            self.stdout.write('')
            self.stdout.write('🚀 Creando nutricionista...')
            
            # Generar schema_name único
            schema_base = re.sub(r'[^a-zA-Z0-9]', '', username.lower())
            schema_name = f"tenant_{schema_base}"
            
            counter = 1
            original_schema = schema_name
            while Tenant.objects.filter(schema_name=schema_name).exists():
                schema_name = f"{original_schema}_{counter}"
                counter += 1

            # Crear usando el servicio
            tenant, domain, user = TenantCreationService.create_complete_tenant(
                schema_name=schema_name,
                tenant_name=name,
                email=email,
                phone='',
                notes='',
                domain_name=domain_name,
                username=username,
                password=password
            )

            # Configurar /etc/hosts si es necesario
            if settings.DEBUG and not skip_hosts:
                self._configure_hosts_file(domain_name)

            # Mostrar resumen de éxito
            self._show_success_summary(name, email, username, password, domain_name, schema_name, tenant.id, user.id)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear nutricionista: {str(e)}')
            )

    def _show_success_summary(self, name, email, username, password, domain_name, schema_name, tenant_id, user_id):
        """Mostrar resumen de éxito"""
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS('🎉 NUTRICIONISTA CREADO EXITOSAMENTE')
        )
        self.stdout.write('='*50)
        self.stdout.write(f'👤 Nutricionista: {name}')
        self.stdout.write(f'📧 Email: {email}')
        self.stdout.write('')
        self.stdout.write('🔐 CREDENCIALES DE ACCESO:')
        self.stdout.write(f'   Username: {username}')
        self.stdout.write(f'   Password: {password}')
        self.stdout.write('')
        self.stdout.write('🌐 ACCESO AL SISTEMA:')
        self.stdout.write(f'   URL directa: http://{domain_name}:8001')
        self.stdout.write(f'   URL general: http://localhost:8001 (redirige automáticamente)')
        self.stdout.write('')
        self.stdout.write('⚙️  INFORMACIÓN TÉCNICA:')
        self.stdout.write(f'   Schema: {schema_name}')
        self.stdout.write(f'   Tenant ID: {tenant_id}')
        self.stdout.write(f'   User ID: {user_id}')
        self.stdout.write('')
        self.stdout.write('🚀 PRÓXIMOS PASOS:')
        self.stdout.write('   1. Acceder con las credenciales mostradas')
        self.stdout.write('   2. Configurar perfil del nutricionista')
        self.stdout.write('   3. ¡Comenzar a usar el sistema!')

    def _configure_hosts_file(self, subdomain):
        """Configura el archivo /etc/hosts para que funcione el subdominio en desarrollo"""
        try:
            # Verificar si ya existe la entrada
            with open('/etc/hosts', 'r') as f:
                hosts_content = f.read()
            
            hosts_entry = f"127.0.0.1    {subdomain}"
            
            if hosts_entry not in hosts_content:
                self.stdout.write('   🔧 Configurando /etc/hosts automáticamente...')
                
                # Usar sudo para agregar la entrada
                if platform.system() == 'Darwin':  # macOS
                    cmd = f'echo "{hosts_entry}" | sudo tee -a /etc/hosts > /dev/null'
                    result = subprocess.run(cmd, shell=True)
                    
                    if result.returncode == 0:
                        self.stdout.write(self.style.SUCCESS(f'   ✅ Agregado a /etc/hosts: {hosts_entry}'))
                    else:
                        self.stdout.write(self.style.WARNING('   ⚠️  Permisos denegados. Agrega manualmente:'))
                        self.stdout.write(f'      sudo echo "{hosts_entry}" >> /etc/hosts')
                else:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  Agrega manualmente a /etc/hosts: {hosts_entry}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'   ✅ /etc/hosts ya contiene: {subdomain}'))
                
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ⚠️  Error configurando /etc/hosts: {str(e)}'))
            self.stdout.write(f'      Agrega manualmente: 127.0.0.1    {subdomain}')
