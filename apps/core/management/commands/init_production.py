from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Inicializa la aplicación para producción sin datos de prueba'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-migrate',
            action='store_true',
            help='Omite las migraciones (si ya están aplicadas)',
        )
        parser.add_argument(
            '--skip-collectstatic',
            action='store_true',
            help='Omite la recolección de archivos estáticos',
        )

    def handle(self, *args, **options):
        environment = os.getenv('ENVIRONMENT', 'development')
        
        if environment != 'production':
            self.stdout.write(
                self.style.WARNING('⚠️  Este comando está diseñado para producción')
            )
            self.stdout.write(f'Entorno actual: {environment}')

        self.stdout.write('🚀 INICIALIZANDO ZENTOERP PARA PRODUCCIÓN')
        self.stdout.write('='*50)

        # Verificar que DEBUG esté en False
        if settings.DEBUG:
            self.stdout.write(
                self.style.ERROR('❌ DEBUG debe estar en False para producción')
            )
            return

        try:
            # Paso 1: Migraciones
            if not options.get('skip_migrate'):
                self.stdout.write('📦 Aplicando migraciones...')
                call_command('migrate_schemas', '--shared', verbosity=0)
                self.stdout.write(self.style.SUCCESS('   ✓ Migraciones aplicadas'))
            else:
                self.stdout.write('⏭️  Migraciones omitidas')

            # Paso 2: Collectstatic
            if not options.get('skip_collectstatic'):
                self.stdout.write('📁 Recolectando archivos estáticos...')
                call_command('collectstatic', '--noinput', verbosity=0)
                self.stdout.write(self.style.SUCCESS('   ✓ Archivos estáticos recolectados'))
            else:
                self.stdout.write('⏭️  Collectstatic omitido')

            # Paso 3: Verificar configuración
            self.stdout.write('🔍 Verificando configuración...')
            self._verify_production_config()

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ ZENTOERP INICIALIZADO CORRECTAMENTE'))
            self.stdout.write('='*50)
            self.stdout.write('📋 PRÓXIMOS PASOS:')
            self.stdout.write('1. Configurar DNS para zentoerp.com y *.zentoerp.com')
            self.stdout.write('2. Crear tenants con: python manage.py create_nutritionist')
            self.stdout.write('3. Verificar funcionamiento en: https://zentoerp.com')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante la inicialización: {str(e)}')
            )

    def _verify_production_config(self):
        """Verifica que la configuración sea apropiada para producción"""
        issues = []
        
        # Verificar DEBUG
        if settings.DEBUG:
            issues.append('DEBUG debe estar en False')
        
        # Verificar SECRET_KEY
        if 'django-insecure' in settings.SECRET_KEY:
            issues.append('SECRET_KEY contiene valor por defecto inseguro')
        
        # Verificar ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
            issues.append('ALLOWED_HOSTS debe estar configurado específicamente')
        
        # Verificar base de datos
        db_engine = settings.DATABASES['default']['ENGINE']
        if 'sqlite' in db_engine:
            issues.append('Base de datos SQLite no recomendada para producción')

        if issues:
            self.stdout.write(self.style.WARNING('   ⚠️  Problemas de configuración encontrados:'))
            for issue in issues:
                self.stdout.write(f'      • {issue}')
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ Configuración verificada'))
