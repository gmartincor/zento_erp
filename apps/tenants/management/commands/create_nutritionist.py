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
        parser.add_argument('--email', type=str, required=True, help='Email del nutricionista')
        parser.add_argument('--username', type=str, required=True, help='Username para login')
        parser.add_argument('--password', type=str, required=True, help='Password para login')
        parser.add_argument('--phone', type=str, help='Teléfono (opcional)')
        parser.add_argument('--professional-number', type=str, help='Número de colegiado (opcional)')
        parser.add_argument('--first-name', type=str, help='Nombre del usuario')
        parser.add_argument('--skip-hosts', action='store_true', help='No configurar /etc/hosts automáticamente')

    def handle(self, *args, **options):
        name = options['name']
        email = options['email']
        username = options['username']
        password = options['password']
        phone = options.get('phone', '')
        professional_number = options.get('professional_number', '')
        first_name = options.get('first_name', '')
        last_name = options.get('last_name', '')
        skip_hosts = options.get('skip_hosts', False)

        try:
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
                phone=phone,
                professional_number=professional_number,
                status=Tenant.StatusChoices.ACTIVE,
                is_active=True
            )

            # Crear el usuario
            if not first_name and not last_name:
                # Si no se proporcionan nombres específicos, usar el nombre completo del nutricionista
                name_parts = name.split()
                first_name = name_parts[0] if name_parts else username
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name or username,  # Asegurar que nunca sea vacío
                last_name=last_name or '',
                tenant=tenant,
                is_active=True
            )

            # Crear dominio para desarrollo
            if settings.DEBUG:
                domain_name = f"{schema_name}.localhost"
            else:
                domain_name = f"{schema_name}.tudominio.com"
            
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
            self.stdout.write(f'🏥 Colegiado: {professional_number or "No especificado"}')
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
                subdomain = f"{schema_name}.localhost"
                
                if not skip_hosts:
                    # Intentar configurar /etc/hosts automáticamente
                    self._configure_hosts_file(subdomain)
                else:
                    self.stdout.write(self.style.WARNING('🔧 CONFIGURACIÓN MANUAL REQUERIDA:'))
                    self.stdout.write(f'   Agregar a /etc/hosts: 127.0.0.1    {subdomain}')

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
