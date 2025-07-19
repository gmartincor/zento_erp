from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant
import getpass


User = get_user_model()


class Command(BaseCommand):
    help = 'Crea un superusuario para desarrollo local de forma interactiva'

    def add_arguments(self, parser):
        parser.add_argument('--non-interactive', action='store_true',
                          help='Modo no interactivo (usar con otros parámetros)')
        parser.add_argument('--prod-creds', action='store_true',
                          help='Crear superuser con credenciales de producción (Guille/Tomatito7)')
        parser.add_argument('--username', type=str, help='Username del superusuario')
        parser.add_argument('--email', type=str, help='Email del superusuario')
        parser.add_argument('--password', type=str, help='Password del superusuario')
        parser.add_argument('--tenant', type=str, default='public',
                          help='Schema del tenant (default: public)')

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔐 CREADOR DE SUPERUSUARIO - DESARROLLO LOCAL')
        )
        self.stdout.write('='*52)
        
        if options.get('prod_creds'):
            # Modo rápido con credenciales de producción
            self._create_with_prod_creds()
        elif options.get('non_interactive'):
            # Modo no interactivo - usar parámetros
            self._create_non_interactive(options)
        else:
            # Modo interactivo - preguntar datos
            self._create_interactive()

    def _create_interactive(self):
        """Modo interactivo para crear superusuario"""
        try:
            self.stdout.write('')
            self.stdout.write('🔑 CONFIGURACIÓN DE SUPERUSUARIO:')
            self.stdout.write('')
            
            # Seleccionar tenant/schema
            self._show_available_schemas()
            tenant_schema = input('📍 Schema [public]: ').strip() or 'public'
            
            # Validar tenant
            if not self._validate_tenant(tenant_schema):
                return
            
            self.stdout.write('')
            self.stdout.write(f'📊 Creando superusuario en schema: {tenant_schema}')
            self.stdout.write('')
            
            self.stdout.write('')
            self.stdout.write('🔑 CONFIGURACIÓN DE SUPERUSUARIO:')
            self.stdout.write('')
            self.stdout.write('💡 Por defecto usará las mismas credenciales que producción:')
            self.stdout.write('   👤 Username: admin')
            self.stdout.write('   🔐 Password: Tomatito7')
            self.stdout.write('   📧 Email: guillermomc007@gmail.com')
            self.stdout.write('')
            self.stdout.write('⚙️  ¿Quieres usar las credenciales de producción o crear otras?')
            
            use_prod_creds = input('🤔 ¿Usar credenciales de producción? (S/n): ').strip().lower()
            
            if use_prod_creds in ['', 's', 'si', 'sí', 'y', 'yes']:
                # Usar credenciales de producción
                username = 'admin'
                password = 'Tomatito7'
                email = input('📧 Email [guillermomc007@gmail.com]: ').strip() or 'guillermomc007@gmail.com'
                
                self.stdout.write('')
                self.stdout.write('✅ Usando credenciales de producción:')
                self.stdout.write(f'   👤 Username: {username}')
                self.stdout.write(f'   📧 Email: {email}')
                self.stdout.write(f'   🔐 Password: {password}')
            else:
                # Pedir credenciales personalizadas
                self.stdout.write('')
                self.stdout.write('🔧 Ingresa credenciales personalizadas:')
                
                username = input('🔑 Username: ').strip()
                if not username:
                    self.stdout.write(self.style.ERROR('❌ El username es requerido'))
                    return
                
                email = input('📧 Email: ').strip()
                if not email:
                    self.stdout.write(self.style.ERROR('❌ El email es requerido'))
                    return
                
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
            self.stdout.write('📋 RESUMEN DEL SUPERUSUARIO:')
            self.stdout.write(f'   🔑 Username: {username}')
            self.stdout.write(f'   📧 Email: {email}')
            self.stdout.write(f'   📍 Schema: {tenant_schema}')
            self.stdout.write('')
            
            confirm = input('¿Crear superusuario? (s/N): ').strip().lower()
            if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
                self.stdout.write(self.style.WARNING('❌ Operación cancelada'))
                return
            
            # Crear superusuario
            self._create_superuser(username, email, password, tenant_schema)
            
        except KeyboardInterrupt:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('❌ Operación cancelada por el usuario'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error inesperado: {str(e)}'))

    def _create_with_prod_creds(self):
        """Crear superuser con credenciales de producción de forma rápida"""
        self.stdout.write('')
        self.stdout.write('🚀 CREANDO SUPERUSER CON CREDENCIALES DE PRODUCCIÓN...')
        self.stdout.write('')
        
        username = 'admin'
        email = 'guillermomc007@gmail.com'
        password = 'Tomatito7'
        tenant_schema = 'public'
        
        self.stdout.write(f'👤 Username: {username}')
        self.stdout.write(f'📧 Email: {email}')
        self.stdout.write(f'🔐 Password: {password}')
        self.stdout.write(f'📍 Schema: {tenant_schema}')
        self.stdout.write('')
        
        self._create_superuser(username, email, password, tenant_schema)

    def _create_non_interactive(self, options):
        """Modo no interactivo usando parámetros"""
        required_fields = ['username', 'email', 'password']
        missing_fields = [field for field in required_fields if not options.get(field)]
        
        if missing_fields:
            self.stdout.write(
                self.style.ERROR(f'❌ Faltan campos requeridos: {", ".join(missing_fields)}')
            )
            return
        
        tenant_schema = options.get('tenant', 'public')
        
        if not self._validate_tenant(tenant_schema):
            return
        
        self._create_superuser(
            options['username'],
            options['email'],
            options['password'],
            tenant_schema
        )

    def _show_available_schemas(self):
        """Mostrar schemas disponibles"""
        self.stdout.write('')
        self.stdout.write('💡 IMPORTANTE: Este superuser será para acceder al ADMIN de Django')
        self.stdout.write('   - NO es para los tenants/nutricionistas')
        self.stdout.write('   - Es como "admin + Tomatito7" en producción')
        self.stdout.write('   - Para tenants usa: create_nutritionist_dev')
        self.stdout.write('')
        self.stdout.write('📁 SCHEMAS DISPONIBLES:')
        
        try:
            tenants = Tenant.objects.all().order_by('schema_name')
            for tenant in tenants:
                if tenant.schema_name in ['public', 'principal']:
                    # Mostrar schemas principales con más detalle
                    self.stdout.write(f'   • {tenant.schema_name} (🌐 {tenant.name})')
                else:
                    # Schemas de tenants específicos
                    self.stdout.write(f'   • {tenant.schema_name} (👤 {tenant.name})')
        except Exception:
            self.stdout.write('   • public (Schema público por defecto)')
            self.stdout.write('   • principal (Schema principal)')
        
        self.stdout.write('')
        self.stdout.write('💡 Para desarrollo local usa "public" (equivale a zentoerp.com en producción)')
        self.stdout.write('💡 Para tenants específicos usa: create_nutritionist_dev')

    def _validate_tenant(self, tenant_schema):
        """Validar que el tenant/schema existe"""
        try:
            if tenant_schema == 'public':
                # Para public schema, buscar el tenant público
                tenant = Tenant.objects.filter(schema_name='public').first()
            else:
                tenant = Tenant.objects.get(schema_name=tenant_schema)
            
            if not tenant:
                self.stdout.write(
                    self.style.ERROR(f'❌ No se encontró el schema: {tenant_schema}')
                )
                return False
            
            return True
            
        except Tenant.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ No se encontró el schema: {tenant_schema}')
            )
            self.stdout.write('💡 Usa uno de los schemas mostrados arriba')
            return False

    def _create_superuser(self, username, email, password, tenant_schema):
        """Crear el superusuario en el schema especificado"""
        try:
            # Obtener el tenant
            if tenant_schema == 'public':
                tenant = Tenant.objects.filter(schema_name='public').first()
            else:
                tenant = Tenant.objects.get(schema_name=tenant_schema)
            
            # Cambiar al contexto del tenant
            with schema_context(tenant_schema):
                self.stdout.write('')
                self.stdout.write(f'🚀 Creando superusuario en schema: {tenant_schema}')
                
                # Verificar si el usuario ya existe
                if User.objects.filter(username=username).exists():
                    self.stdout.write(
                        self.style.ERROR(f'❌ El usuario {username} ya existe en {tenant_schema}')
                    )
                    return
                
                # Crear el superusuario SIN asociar a tenant específico
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                
                # Los superusers NO se asocian a tenants específicos
                # Esto les permite acceder al admin global
                
                # Mostrar resumen de éxito
                self._show_success_summary(username, email, tenant_schema, tenant)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear superusuario: {str(e)}')
            )

    def _show_success_summary(self, username, email, tenant_schema, tenant):
        """Mostrar resumen de éxito"""
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS('🎉 SUPERUSUARIO CREADO EXITOSAMENTE')
        )
        self.stdout.write('='*50)
        self.stdout.write(f'🔑 Username: {username}')
        self.stdout.write(f'📧 Email: {email}')
        self.stdout.write(f'📍 Schema: {tenant_schema}')
        self.stdout.write(f'🏥 Tenant: {tenant.name if tenant else "Sin tenant"}')
        self.stdout.write('')
        self.stdout.write('🌐 ACCESO AL SISTEMA:')
        
        if tenant_schema == 'public':
            self.stdout.write('   🏠 Admin Django: http://localhost:8001/admin/')
            self.stdout.write('   🌐 Aplicación: http://localhost:8001/')
        elif tenant_schema == 'principal':
            self.stdout.write('   🏠 Admin Django: http://principal.localhost:8001/admin/')
            self.stdout.write('   🌐 Aplicación: http://principal.localhost:8001/')
        else:
            # Para otros tenants, mostrar sus dominios
            try:
                domains = tenant.domains.all() if tenant else []
                localhost_domains = [d.domain for d in domains if 'localhost' in d.domain]
                if localhost_domains:
                    domain = localhost_domains[0]
                    self.stdout.write(f'   🏠 Admin Django: http://{domain}:8001/admin/')
                    self.stdout.write(f'   🌐 Aplicación: http://{domain}:8001/')
                else:
                    self.stdout.write(f'   ⚠️  Schema {tenant_schema} no tiene dominios localhost configurados')
            except Exception:
                self.stdout.write(f'   📍 Schema: {tenant_schema} (configurar dominio manualmente)')
        
        self.stdout.write('')
        self.stdout.write('🚀 PRÓXIMOS PASOS:')
        self.stdout.write('   1. Acceder al admin con las credenciales creadas')
        self.stdout.write('   2. Configurar usuarios y tenants desde el admin')
        self.stdout.write('   3. ¡Administrar el sistema!')
        self.stdout.write('')
        self.stdout.write('💡 NOTA: Este superusuario tiene acceso completo al admin de Django')
