from django.core.management.base import BaseCommand
from django.conf import settings
from apps.tenants.models import Tenant, Domain
from apps.authentication.models import User
import re
import subprocess
import platform


class Command(BaseCommand):
    help = 'Crea un nuevo nutricionista con su tenant y usuario'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, required=True, help='Nombre del nutricionista')
        parser.add_argument('--username', type=str, required=True, help='Username para login')
        parser.add_argument('--password', type=str, required=True, help='Password para login')
        parser.add_argument('--email', type=str, required=True, help='Email del nutricionista')
        parser.add_argument('--domain', type=str, required=True, help='Dominio (ej: carlos.localhost)')
        parser.add_argument('--skip-hosts', action='store_true', help='No configurar /etc/hosts automáticamente')

    def handle(self, *args, **options):
        name = options['name']
        username = options['username']
        password = options['password']
        email = options['email']
        domain_name = options['domain']
        skip_hosts = options.get('skip_hosts', False)

        try:
            # Verificar que el dominio no exista
            if Domain.objects.filter(domain=domain_name).exists():
                self.stdout.write(
                    self.style.ERROR(f'❌ El dominio "{domain_name}" ya está registrado')
                )
                return

            # Verificar que el username no exista
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.ERROR(f'❌ El username "{username}" ya existe')
                )
                return

            # Verificar que el email no exista
            if Tenant.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.ERROR(f'❌ El email "{email}" ya está registrado')
                )
                return

            # Generar schema_name único
            schema_base = re.sub(r'[^a-zA-Z0-9]', '', username.lower())
            schema_name = f"tenant_{schema_base}"
            
            counter = 1
            original_schema = schema_name
            while Tenant.objects.filter(schema_name=schema_name).exists():
                schema_name = f"{original_schema}_{counter}"
                counter += 1

            # Crear el tenant
            tenant = Tenant.objects.create(
                schema_name=schema_name,
                name=name,
                email=email,
                phone='',  # Campo opcional vacío
                professional_number='',  # Campo opcional vacío
                status=Tenant.StatusChoices.ACTIVE,
                is_active=True
            )

            # Crear el usuario
            # Usar el nombre completo del nutricionista para first_name y last_name
            name_parts = name.split()
            first_name = name_parts[0] if name_parts else username
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                tenant=tenant,
                is_active=True
            )

            # Crear dominio usando el dominio proporcionado
            domain = Domain.objects.create(
                domain=domain_name,
                tenant=tenant,
                is_primary=True
            )

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
            self.stdout.write(f'   URL directa: http://{domain_name}')
            self.stdout.write(f'   URL general: http://localhost:8000 (se redirige automáticamente)')
            self.stdout.write('')
            self.stdout.write('⚙️  INFORMACIÓN TÉCNICA:')
            self.stdout.write(f'   Schema: {schema_name}')
            self.stdout.write(f'   Tenant ID: {tenant.id}')
            self.stdout.write(f'   User ID: {user.id}')

            if settings.DEBUG:
                self.stdout.write('')
                # Usar el dominio proporcionado para /etc/hosts
                if not skip_hosts:
                    # Intentar configurar /etc/hosts automáticamente
                    self._configure_hosts_file(domain_name)
                else:
                    self.stdout.write(self.style.WARNING('🔧 CONFIGURACIÓN MANUAL REQUERIDA:'))
                    self.stdout.write(f'   Agregar a /etc/hosts: 127.0.0.1    {domain_name}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear nutricionista: {str(e)}')
            )

    def _configure_hosts_file(self, subdomain):
        """Configura el archivo /etc/hosts para que funcione el subdominio en desarrollo"""
        try:
            # Verificar si ya existe la entrada
            with open('/etc/hosts', 'r') as f:
                hosts_content = f.read()
            
            hosts_entry = f"127.0.0.1    {subdomain}"
            
            if hosts_entry not in hosts_content:
                self.stdout.write('🔧 Configurando /etc/hosts automáticamente...')
                
                # Usar sudo para agregar la entrada
                if platform.system() == 'Darwin':  # macOS
                    cmd = f'echo "{hosts_entry}" | sudo tee -a /etc/hosts > /dev/null'
                    result = subprocess.run(cmd, shell=True)
                    
                    if result.returncode == 0:
                        self.stdout.write(self.style.SUCCESS(f'✅ Agregado a /etc/hosts: {hosts_entry}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'⚠️  Permisos denegados. Agrega manualmente:'))
                        self.stdout.write(f'   sudo echo "{hosts_entry}" >> /etc/hosts')
                else:
                    self.stdout.write(self.style.WARNING(f'⚠️  Agrega manualmente a /etc/hosts: {hosts_entry}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'✅ /etc/hosts ya contiene: {subdomain}'))
                
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  Error configurando /etc/hosts: {str(e)}'))
            self.stdout.write(f'   Agrega manualmente: 127.0.0.1    {subdomain}')
