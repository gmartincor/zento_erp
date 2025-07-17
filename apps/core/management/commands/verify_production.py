"""
Comando para verificar que la configuración de producción esté correcta
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from django.core.cache import cache
import os
import sys


class Command(BaseCommand):
    help = 'Verifica la configuración de producción'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                '🔍 Verificando configuración de producción para zentoerp.com\n'
                '=' * 60
            )
        )

        errors = []
        warnings = []

        # Verificar configuración básica
        self.check_basic_settings(errors, warnings)
        
        # Verificar base de datos
        self.check_database(errors, warnings)
        
        # Verificar cache
        self.check_cache(errors, warnings)
        
        # Verificar configuración multi-tenant
        self.check_tenant_config(errors, warnings)
        
        # Verificar archivos estáticos
        self.check_static_files(errors, warnings)

        # Mostrar resumen
        self.show_summary(errors, warnings)

    def check_basic_settings(self, errors, warnings):
        self.stdout.write('\n📋 Configuración básica:')
        
        # DEBUG
        if settings.DEBUG:
            errors.append('DEBUG está activado en producción')
        else:
            self.stdout.write(self.style.SUCCESS('✅ DEBUG: False'))

        # SECRET_KEY
        if not settings.SECRET_KEY or settings.SECRET_KEY == 'django-insecure-change-this-in-production':
            errors.append('SECRET_KEY no está configurada correctamente')
        else:
            self.stdout.write(self.style.SUCCESS('✅ SECRET_KEY: Configurada'))

        # ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
            errors.append('ALLOWED_HOSTS no está configurado para producción')
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}'))

    def check_database(self, errors, warnings):
        self.stdout.write('\n🗄️  Base de datos:')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(self.style.SUCCESS('✅ Conexión a base de datos: OK'))
                
                # Verificar configuración
                db_config = settings.DATABASES['default']
                if db_config['ENGINE'] != 'django_tenants.postgresql_backend':
                    errors.append('Motor de base de datos no es django_tenants.postgresql_backend')
                else:
                    self.stdout.write(self.style.SUCCESS('✅ Motor de DB: django_tenants.postgresql_backend'))
                
                if 'sslmode' not in db_config.get('OPTIONS', {}):
                    warnings.append('SSL no está configurado para la base de datos')
                else:
                    self.stdout.write(self.style.SUCCESS('✅ SSL de DB: Configurado'))
                    
        except Exception as e:
            errors.append(f'Error de conexión a base de datos: {str(e)}')

    def check_cache(self, errors, warnings):
        self.stdout.write('\n🔄 Cache:')
        
        try:
            cache.set('test_key', 'test_value', 30)
            value = cache.get('test_key')
            if value == 'test_value':
                self.stdout.write(self.style.SUCCESS('✅ Cache Redis: Funcionando'))
            else:
                errors.append('Cache Redis no está funcionando correctamente')
        except Exception as e:
            errors.append(f'Error de cache: {str(e)}')

    def check_tenant_config(self, errors, warnings):
        self.stdout.write('\n🏢 Configuración multi-tenant:')
        
        # Verificar modelos
        if not hasattr(settings, 'TENANT_MODEL'):
            errors.append('TENANT_MODEL no está configurado')
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ TENANT_MODEL: {settings.TENANT_MODEL}'))

        if not hasattr(settings, 'TENANT_DOMAIN_MODEL'):
            errors.append('TENANT_DOMAIN_MODEL no está configurado')
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ TENANT_DOMAIN_MODEL: {settings.TENANT_DOMAIN_MODEL}'))

        # Verificar dominio
        if hasattr(settings, 'TENANT_DOMAIN'):
            self.stdout.write(self.style.SUCCESS(f'✅ TENANT_DOMAIN: {settings.TENANT_DOMAIN}'))
        else:
            warnings.append('TENANT_DOMAIN no está configurado')

    def check_static_files(self, errors, warnings):
        self.stdout.write('\n📦 Archivos estáticos:')
        
        if not settings.STATIC_ROOT:
            errors.append('STATIC_ROOT no está configurado')
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ STATIC_ROOT: {settings.STATIC_ROOT}'))

        if not os.path.exists(settings.STATIC_ROOT):
            warnings.append('Directorio STATIC_ROOT no existe (ejecutar collectstatic)')
        else:
            self.stdout.write(self.style.SUCCESS('✅ Directorio de archivos estáticos: Existe'))

    def show_summary(self, errors, warnings):
        self.stdout.write('\n' + '=' * 60)
        
        if errors:
            self.stdout.write(self.style.ERROR(f'❌ {len(errors)} ERROR(ES) ENCONTRADO(S):'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'   • {error}'))
        
        if warnings:
            self.stdout.write(self.style.WARNING(f'⚠️  {len(warnings)} ADVERTENCIA(S):'))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f'   • {warning}'))
        
        if not errors and not warnings:
            self.stdout.write(
                self.style.SUCCESS(
                    '🎉 ¡Configuración de producción verificada exitosamente!\n'
                    '   La aplicación está lista para zentoerp.com'
                )
            )
        elif not errors:
            self.stdout.write(
                self.style.SUCCESS(
                    '✅ Configuración básica correcta con algunas advertencias\n'
                    '   La aplicación puede desplegarse en producción'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    '❌ La configuración tiene errores críticos\n'
                    '   Corregir antes de desplegar en producción'
                )
            )
            sys.exit(1)
