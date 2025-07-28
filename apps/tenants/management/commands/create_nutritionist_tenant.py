
from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.management import call_command
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant, Domain
from apps.authentication.models import User
import re
import getpass


class Command(BaseCommand):
    help = 'Crea un nuevo tenant completo con dominio, usuario y configuración'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        # Comando completamente interactivo
        self._run_interactive_mode()

    def _run_interactive_mode(self):
        """Ejecuta el comando en modo interactivo"""
        self.stdout.write(self.style.SUCCESS('🏥 CRM NUTRICIÓN PRO - CREACIÓN INTERACTIVA DE TENANT'))
        self.stdout.write('=' * 60)
        
        try:
            self.stdout.write('')
            self.stdout.write('📝 Ingresa los datos del nuevo tenant:')
            self.stdout.write('')
            
            # Obtener datos del tenant de forma interactiva
            tenant_data = self._get_tenant_data_interactive()
            
            # Mostrar resumen y confirmar
            self._show_tenant_summary(tenant_data)
            if not self._confirm_creation():
                self.stdout.write(self.style.WARNING('❌ Creación cancelada'))
                return
            
            # Crear el tenant
            self._create_tenant_with_data(tenant_data)
            
        except KeyboardInterrupt:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('❌ Operación cancelada por el usuario'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear tenant: {str(e)}')
            )



    def _get_tenant_data_interactive(self):
        """Obtiene los datos del tenant de forma interactiva"""
        tenant_data = {}
        
        # Schema name
        while True:
            schema_name = input('🏷️  Schema name (ej: carlos, maria-nutricion): ').strip().lower()
            if self._validate_schema_name(schema_name):
                tenant_data['schema_name'] = schema_name
                break
            else:
                self.stdout.write(self.style.ERROR('   ❌ Schema name inválido. Debe empezar con letra y solo contener letras minúsculas, números y guiones bajos'))
        
        # Domain name
        while True:
            domain_name = input('🌐 Dominio (ej: carlos.zentoerp.com): ').strip().lower()
            if self._validate_domain_name(domain_name):
                tenant_data['domain_name'] = domain_name
                break
            else:
                self.stdout.write(self.style.ERROR('   ❌ Dominio inválido. Debe ser un subdominio de zentoerp.com'))
        
        # Tenant name
        tenant_name = input('🏥 Nombre del tenant (ej: Carlos Nutricionista): ').strip()
        tenant_data['tenant_name'] = tenant_name
        
        # Email
        while True:
            email = input('📧 Email del tenant: ').strip().lower()
            if self._validate_email(email):
                tenant_data['email'] = email
                break
            else:
                self.stdout.write(self.style.ERROR('   ❌ Email inválido o ya existe'))
        
        # Username
        username = input(f'👤 Username (default: {tenant_data["schema_name"]}): ').strip()
        tenant_data['username'] = username if username else tenant_data["schema_name"]
        
        # Password
        password = getpass.getpass('🔐 Password (default: changeme123): ')
        tenant_data['password'] = password if password else 'changeme123'
        
        # Phone
        phone = input('📞 Teléfono (opcional): ').strip()
        tenant_data['phone'] = phone
        
        # Notes
        notes = input('📝 Notas adicionales (opcional): ').strip()
        tenant_data['notes'] = notes
        
        return tenant_data

    def _validate_schema_name(self, schema_name):
        """Valida el schema name"""
        if not re.match(r'^[a-z][a-z0-9_]*$', schema_name):
            return False
        try:
            return not Tenant.objects.filter(schema_name=schema_name).exists()
        except:
            return True  # Si no hay conexión, asumir que es válido

    def _validate_domain_name(self, domain_name):
        """Valida el domain name"""
        if not re.match(r'^[a-z0-9.-]+\.zentoerp\.com$', domain_name):
            return False
        try:
            return not Domain.objects.filter(domain=domain_name).exists()
        except:
            return True  # Si no hay conexión, asumir que es válido

    def _validate_email(self, email):
        """Valida el email"""
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return False
        try:
            return not Tenant.objects.filter(email=email).exists()
        except:
            return True  # Si no hay conexión, asumir que es válido

    def _show_tenant_summary(self, tenant_data):
        """Muestra un resumen de los datos del tenant"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('📋 RESUMEN DEL TENANT A CREAR'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'🏷️  Schema: {tenant_data["schema_name"]}')
        self.stdout.write(f'🌐 Dominio: {tenant_data["domain_name"]}')
        self.stdout.write(f'🏥 Nombre: {tenant_data["tenant_name"]}')
        self.stdout.write(f'📧 Email: {tenant_data["email"]}')
        self.stdout.write(f'👤 Username: {tenant_data["username"]}')
        self.stdout.write(f'📞 Teléfono: {tenant_data["phone"] or "No especificado"}')
        self.stdout.write(f'📝 Notas: {tenant_data["notes"] or "No especificado"}')
        self.stdout.write('=' * 60)

    def _confirm_creation(self):
        """Confirma la creación del tenant"""
        while True:
            confirm = input('\n¿Proceder con la creación del tenant? (y/N): ').strip().lower()
            if confirm in ['y', 'yes', 's', 'si']:
                return True
            elif confirm in ['n', 'no', '']:
                return False
            else:
                self.stdout.write('   Por favor responde "y" para sí o "n" para no')

    def _create_tenant_with_data(self, tenant_data):
        """Crea el tenant con los datos proporcionados"""
        self.stdout.write('\n🚀 Iniciando creación del tenant...')
        
        try:
            with transaction.atomic():
                # 1. Crear tenant
                tenant = self._create_tenant(
                    tenant_data['schema_name'],
                    tenant_data['tenant_name'],
                    tenant_data['email'],
                    tenant_data['phone'],
                    tenant_data['notes']
                )
                
                # 2. Crear dominio
                domain = self._create_domain(tenant_data['domain_name'], tenant)
                
                # 3. Aplicar migraciones al nuevo schema
                self._migrate_tenant_schema(tenant)
                
                # 4. Crear usuario admin para el tenant
                user = self._create_tenant_user(
                    tenant,
                    tenant_data['username'],
                    tenant_data['email'],
                    tenant_data['password']
                )
                
                # 5. Mostrar resumen de éxito
                self._show_success_summary(tenant, domain, user, tenant_data['password'])
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante la creación: {str(e)}')
            )
            raise



    def _create_tenant(self, schema_name, tenant_name, tenant_email, phone, notes):
        """Crea el tenant"""
        self.stdout.write('📋 Creando tenant...')
        tenant = Tenant.objects.create(
            schema_name=schema_name,
            name=tenant_name,
            email=tenant_email,
            phone=phone,
            notes=notes,
            status=Tenant.StatusChoices.ACTIVE,
            is_active=True
        )
        self.stdout.write(f'   ✅ Tenant "{tenant_name}" creado')
        return tenant

    def _create_domain(self, domain_name, tenant):
        """Crea el dominio para el tenant"""
        self.stdout.write('🌐 Creando dominio...')
        domain = Domain.objects.create(
            domain=domain_name,
            tenant=tenant,
            is_primary=True
        )
        self.stdout.write(f'   ✅ Dominio "{domain_name}" creado')
        return domain

    def _migrate_tenant_schema(self, tenant):
        """Aplica migraciones al schema del tenant"""
        self.stdout.write('📦 Aplicando migraciones al schema...')
        try:
            call_command('migrate_schemas', '--tenant', verbosity=0)
            self.stdout.write('   ✅ Migraciones aplicadas')
        except Exception as e:
            self.stdout.write(f'   ⚠️ Error en migraciones: {str(e)}')

    def _create_tenant_user(self, tenant, username, email, password):
        """Crea el usuario principal para el tenant (NO admin del sistema)"""
        self.stdout.write('👤 Creando usuario principal del tenant...')
        
        with schema_context(tenant.schema_name):
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=False,  
                is_superuser=False,  
                tenant=tenant
            )
            self.stdout.write(f'   ✅ Usuario "{username}" creado')
            return user

    def _show_success_summary(self, tenant, domain, user, password):
        """Muestra el resumen de éxito"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🎉 TENANT CREADO EXITOSAMENTE'))
        self.stdout.write('='*60)
        self.stdout.write(f'🏥 Tenant: {tenant.name}')
        self.stdout.write(f'📍 Schema: {tenant.schema_name}')
        self.stdout.write(f'🌐 Dominio: {domain.domain}')
        self.stdout.write(f'📧 Email: {tenant.email}')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('👤 CREDENCIALES DE ACCESO:'))
        self.stdout.write(f'   Username: {user.username}')
        self.stdout.write(f'   Password: {password}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🌍 ACCESO:'))
        self.stdout.write(f'   https://{domain.domain}/')
        self.stdout.write(f'   https://{domain.domain}/admin/')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('⚠️  IMPORTANTE:'))
        self.stdout.write('   • Cambia la contraseña después del primer login')
        self.stdout.write('   • Verifica que el DNS esté configurado')
        self.stdout.write('   • El tenant está activo y listo para usar')
