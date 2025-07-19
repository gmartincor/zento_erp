from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.apps import apps
import os
import sys


class Command(BaseCommand):
    help = 'Resetea migraciones después de sincronizar con producción'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fake-initial',
            action='store_true',
            help='Marcar migraciones iniciales como fake',
        )
        parser.add_argument(
            '--list-migrations',
            action='store_true',
            help='Solo listar estado de migraciones',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 RESETEO DE MIGRACIONES POST-SINCRONIZACIÓN'))
        self.stdout.write('=' * 60)

        if options['list_migrations']:
            self.list_migrations()
            return

        try:
            # 1. Verificar que estamos en desarrollo
            from django.conf import settings
            if not settings.DEBUG:
                self.stdout.write(
                    self.style.ERROR('❌ Este comando solo debe ejecutarse en desarrollo (DEBUG=True)')
                )
                sys.exit(1)

            # 2. Listar migraciones actuales
            self.stdout.write('\n📋 Estado actual de migraciones:')
            self.list_migrations()

            # 3. Confirmar la operación
            confirm = input('\n¿Continuar con el reseteo de migraciones? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING('❌ Operación cancelada'))
                return

            # 4. Resetear migraciones fake
            self.stdout.write('\n🔄 Reseteando migraciones...')
            
            # Para django-tenants, necesitamos manejar tanto shared como tenant apps
            self.reset_migrations_for_tenants()

            self.stdout.write(self.style.SUCCESS('\n✅ Reseteo de migraciones completado'))
            self.stdout.write('\n🚀 Próximos pasos:')
            self.stdout.write('   1. Verificar que la app funciona correctamente')
            self.stdout.write('   2. Crear nuevas migraciones si es necesario')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante el reseteo: {str(e)}')
            )
            sys.exit(1)

    def list_migrations(self):
        """Lista el estado actual de las migraciones"""
        try:
            # Obtener estado de migraciones
            call_command('showmigrations', verbosity=1)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al listar migraciones: {str(e)}')
            )

    def reset_migrations_for_tenants(self):
        """Resetea migraciones para django-tenants"""
        
        # Obtener todas las apps con migraciones
        django_apps = apps.get_app_configs()
        
        # Apps que típicamente tienen migraciones compartidas (shared)
        shared_apps = [
            'tenants',
            'authentication', 
            'django_tenants',
            'contenttypes',
            'auth',
            'admin',
            'sessions',
        ]
        
        # Apps que son específicas de tenant
        tenant_apps = [
            'accounting',
            'invoicing', 
            'business_lines',
            'dashboard',
            'expenses',
            'core',
        ]

        self.stdout.write('\n🏢 Reseteando migraciones compartidas (shared)...')
        try:
            # Resetear migraciones compartidas
            call_command('migrate_schemas', '--shared', '--fake', verbosity=1)
            self.stdout.write(self.style.SUCCESS('✅ Migraciones compartidas reseteadas'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  Advertencia en migraciones compartidas: {str(e)}'))

        self.stdout.write('\n🏘️  Reseteando migraciones de tenants...')
        try:
            # Resetear migraciones de tenants
            call_command('migrate_schemas', '--fake', verbosity=1)
            self.stdout.write(self.style.SUCCESS('✅ Migraciones de tenants reseteadas'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  Advertencia en migraciones de tenants: {str(e)}'))

        # Verificar estado final
        self.stdout.write('\n📊 Estado final de migraciones:')
        self.list_migrations()

    def check_database_tables(self):
        """Verifica qué tablas existen en la base de datos"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            self.stdout.write('\n📋 Tablas en la base de datos:')
            for table in tables:
                self.stdout.write(f'   • {table[0]}')
