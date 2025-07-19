
from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.management import call_command
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant, Domain
from apps.authentication.models import User
import re


class Command(BaseCommand):
    help = 'Crea un nuevo tenant completo con dominio, usuario y configuración'

    def add_arguments(self, parser):
        parser.add_argument(
            'schema_name',
            type=str,
            help='Nombre del schema del tenant (ej: carlos, maria-nutricion)'
        )
        parser.add_argument(
            'domain_name',
            type=str,
            help='Nombre del dominio (ej: carlos.zentoerp.com, maria.zentoerp.com)'
        )
        parser.add_argument(
            'tenant_name',
            type=str,
            help='Nombre del tenant (ej: Carlos Nutricionista, María Pérez)'
        )
        parser.add_argument(
            'tenant_email',
            type=str,
            help='Email del tenant (ej: carlos@ejemplo.com)'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username para el usuario admin del tenant (default: usar schema_name)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='changeme123',
            help='Password inicial (default: changeme123)'
        )
        parser.add_argument(
            '--phone',
            type=str,
            default='',
            help='Teléfono del tenant'
        )
        parser.add_argument(
            '--notes',
            type=str,
            default='',
            help='Notas adicionales del tenant'
        )

    def handle(self, *args, **options):
        schema_name = options['schema_name']
        domain_name = options['domain_name']
        tenant_name = options['tenant_name']
        tenant_email = options['tenant_email']
        username = options.get('username') or schema_name
        password = options['password']
        phone = options['phone']
        notes = options['notes']

        # Validaciones
        if not self._validate_inputs(schema_name, domain_name, tenant_email, username):
            return

        try:
            with transaction.atomic():
                self.stdout.write('🚀 Creando tenant completo...')
                
                # 1. Crear tenant
                tenant = self._create_tenant(schema_name, tenant_name, tenant_email, phone, notes)
                
                # 2. Crear dominio
                domain = self._create_domain(domain_name, tenant)
                
                # 3. Aplicar migraciones al nuevo schema
                self._migrate_tenant_schema(tenant)
                
                # 4. Crear usuario admin para el tenant
                user = self._create_tenant_user(tenant, username, tenant_email, password)
                
                # 5. Mostrar resumen
                self._show_success_summary(tenant, domain, user, password)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear tenant: {str(e)}')
            )

    def _validate_inputs(self, schema_name, domain_name, email, username):
        """Valida que los inputs sean correctos"""
        errors = []
        
        # Validar schema_name
        if not re.match(r'^[a-z][a-z0-9_]*$', schema_name):
            errors.append('Schema name debe empezar con letra y solo contener letras minúsculas, números y guiones bajos')
        
        if Tenant.objects.filter(schema_name=schema_name).exists():
            errors.append(f'Ya existe un tenant con schema "{schema_name}"')
        
        # Validar domain_name
        if not re.match(r'^[a-z0-9.-]+\.zentoerp\.com$', domain_name):
            errors.append('El dominio debe ser un subdominio de zentoerp.com (ej: carlos.zentoerp.com)')
        
        if Domain.objects.filter(domain=domain_name).exists():
            errors.append(f'Ya existe el dominio "{domain_name}"')
        
        # Validar email
        if Tenant.objects.filter(email=email).exists():
            errors.append(f'Ya existe un tenant con email "{email}"')
        
        if errors:
            self.stdout.write(self.style.ERROR('❌ Errores de validación:'))
            for error in errors:
                self.stdout.write(f'   • {error}')
            return False
        
        return True

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
        """Crea el usuario admin para el tenant"""
        self.stdout.write('👤 Creando usuario admin...')
        
        with schema_context(tenant.schema_name):
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True,
                is_superuser=True,
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
