from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Limpia la base de datos de todos los datos de prueba para preparar producción'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma que quieres eliminar todos los datos de prueba',
        )
        parser.add_argument(
            '--environment',
            type=str,
            default='development',
            help='Especifica el entorno (development/production)',
        )

    def handle(self, *args, **options):
        if not options.get('confirm', False):
            self.stdout.write(
                self.style.ERROR('⚠️  ADVERTENCIA: Este comando eliminará TODOS los datos de prueba.')
            )
            self.stdout.write(
                self.style.ERROR('Para confirmar, ejecuta: python manage.py cleanup_production --confirm')
            )
            return

        environment = options.get('environment', 'development')
        
        if environment == 'production' and settings.DEBUG:
            self.stdout.write(
                self.style.ERROR('❌ No se puede ejecutar limpieza de producción con DEBUG=True')
            )
            return

        self.stdout.write('🧹 Iniciando limpieza de datos de prueba...')
        
        try:
            with transaction.atomic():
                self._cleanup_test_users()
                self._cleanup_test_clients()
                self._cleanup_test_business_lines()
                self._cleanup_test_expenses()
                
            self.stdout.write(self.style.SUCCESS('✅ Limpieza completada exitosamente'))
            self.stdout.write('')
            self.stdout.write('📋 BASE DE DATOS LISTA PARA PRODUCCIÓN')
            self.stdout.write('='*50)
            self.stdout.write('• Usuarios de prueba eliminados')
            self.stdout.write('• Clientes ficticios eliminados')
            self.stdout.write('• Líneas de negocio de prueba eliminadas')
            self.stdout.write('• Gastos de prueba eliminados')
            self.stdout.write('')
            self.stdout.write('⚠️  IMPORTANTE: Ejecuta las migraciones antes del primer deploy:')
            self.stdout.write('   python manage.py migrate_schemas --shared')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante la limpieza: {str(e)}')
            )

    def _cleanup_test_users(self):
        """Elimina usuarios de prueba pero mantiene estructura de auth"""
        self.stdout.write('🔄 Limpiando usuarios de prueba...')
        
        # Eliminar usuarios específicos de prueba (mantener superusers en desarrollo)
        test_usernames = ['maria.glow', 'carlos.glow', 'admin']
        
        # En producción, eliminar todo excepto si hay superusers existentes
        if not settings.DEBUG:
            User.objects.filter(username__in=test_usernames).delete()
            self.stdout.write('   ✓ Usuarios de prueba eliminados')
        else:
            self.stdout.write('   ⚠️  Modo desarrollo: usuarios mantenidos')

    def _cleanup_test_clients(self):
        """Elimina clientes de prueba"""
        self.stdout.write('🔄 Limpiando clientes de prueba...')
        
        try:
            from apps.accounting.models import Client, ClientService
            
            # Identificar clientes de prueba por patrones comunes
            test_patterns = [
                'test', 'prueba', 'ejemplo', 'demo', 'ficticio',
                '@example.com', '@test.com', '@demo.com'
            ]
            
            deleted_clients = 0
            deleted_services = 0
            
            for pattern in test_patterns:
                # Eliminar servicios asociados primero
                services = ClientService.objects.filter(
                    client__email__icontains=pattern
                )
                deleted_services += services.count()
                services.delete()
                
                # Eliminar clientes
                clients = Client.objects.filter(email__icontains=pattern)
                deleted_clients += clients.count()
                clients.delete()
            
            self.stdout.write(f'   ✓ {deleted_clients} clientes y {deleted_services} servicios eliminados')
            
        except ImportError:
            self.stdout.write('   ⚠️  Módulo accounting no disponible')

    def _cleanup_test_business_lines(self):
        """Elimina líneas de negocio de prueba"""
        self.stdout.write('🔄 Limpiando líneas de negocio de prueba...')
        
        try:
            from apps.business_lines.models import BusinessLine
            
            # Solo eliminar líneas claramente marcadas como prueba
            test_lines = BusinessLine.objects.filter(
                name__icontains='test'
            ) | BusinessLine.objects.filter(
                name__icontains='prueba'
            )
            
            deleted_count = test_lines.count()
            test_lines.delete()
            
            self.stdout.write(f'   ✓ {deleted_count} líneas de negocio de prueba eliminadas')
            
        except ImportError:
            self.stdout.write('   ⚠️  Módulo business_lines no disponible')

    def _cleanup_test_expenses(self):
        """Elimina gastos de prueba"""
        self.stdout.write('🔄 Limpiando gastos de prueba...')
        
        try:
            from apps.expenses.models import Expense, ExpenseCategory
            
            # Eliminar gastos con descripciones de prueba
            test_expenses = Expense.objects.filter(
                description__icontains='test'
            ) | Expense.objects.filter(
                description__icontains='prueba'
            )
            
            deleted_expenses = test_expenses.count()
            test_expenses.delete()
            
            # Eliminar categorías de prueba
            test_categories = ExpenseCategory.objects.filter(
                name__icontains='test'
            ) | ExpenseCategory.objects.filter(
                name__icontains='prueba'
            )
            
            deleted_categories = test_categories.count()
            test_categories.delete()
            
            self.stdout.write(f'   ✓ {deleted_expenses} gastos y {deleted_categories} categorías eliminadas')
            
        except ImportError:
            self.stdout.write('   ⚠️  Módulo expenses no disponible')
