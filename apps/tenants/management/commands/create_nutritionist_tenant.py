
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.tenants.models import Tenant, Domain
from apps.tenants.services import TenantCreationService
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
        try:
            return TenantCreationService.validate_schema_name(schema_name)
        except Exception:
            return False

    def _validate_domain_name(self, domain_name):
        try:
            TenantCreationService.validate_domain_name(domain_name)
            return True
        except Exception:
            return False

    def _validate_email(self, email):
        try:
            TenantCreationService.validate_email(email)
            return True
        except Exception:
            return False

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
        self.stdout.write('\n🚀 Iniciando creación del tenant...')
        
        try:
            tenant, domain, user = TenantCreationService.create_complete_tenant(
                schema_name=tenant_data['schema_name'],
                tenant_name=tenant_data['tenant_name'],
                email=tenant_data['email'],
                phone=tenant_data['phone'],
                notes=tenant_data['notes'],
                domain_name=tenant_data['domain_name'],
                username=tenant_data['username'],
                password=tenant_data['password']
            )
            
            self._show_success_summary(tenant, domain, user, tenant_data['password'])
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante la creación: {str(e)}')
            )
            raise



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
