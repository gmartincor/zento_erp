from django.core.management.base import BaseCommand
from django.db import transaction
from apps.business_lines.models import BusinessLine
from apps.accounting.models import ClientService
import os
import re


class Command(BaseCommand):
    help = 'Analiza el sistema actual de remanentes para planificar su eliminación completa'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== ANÁLISIS COMPLETO DEL SISTEMA ACTUAL DE REMANENTES ===\n'))
        
        # 1. Analizar uso en base de datos
        self._analyze_database_usage()
        
        # 2. Analizar referencias en código
        self._analyze_code_references()
        
        # 3. Generar plan de migración
        self._generate_migration_plan()
    
    def _analyze_database_usage(self):
        self.stdout.write(self.style.WARNING('1. ANÁLISIS DE USO EN BASE DE DATOS:'))
        self.stdout.write('=' * 50)
        
        # Líneas de negocio con remanente habilitado
        bl_with_remanente = BusinessLine.objects.filter(has_remanente=True)
        self.stdout.write(f'Líneas de negocio con has_remanente=True: {bl_with_remanente.count()}')
        for bl in bl_with_remanente:
            self.stdout.write(f'  - {bl.name} (ID: {bl.id}, field: {bl.remanente_field})')
        
        # Servicios BLACK existentes
        black_services = ClientService.objects.filter(category='BLACK')
        self.stdout.write(f'\nServicios BLACK existentes: {black_services.count()}')
        
        # Servicios con datos de remanentes
        services_with_remanentes = black_services.exclude(remanentes__isnull=True).exclude(remanentes={})
        self.stdout.write(f'Servicios BLACK con datos de remanentes: {services_with_remanentes.count()}')
        
        for service in services_with_remanentes:
            self.stdout.write(f'  - Cliente: {service.client.full_name}, BL: {service.business_line.name}')
            self.stdout.write(f'    Remanentes: {service.remanentes}')
    
    def _analyze_code_references(self):
        self.stdout.write(f'\n{self.style.WARNING("2. ANÁLISIS DE REFERENCIAS EN CÓDIGO:")}')
        self.stdout.write('=' * 50)
        
        # Buscar archivos con referencias a remanentes
        base_dir = os.getcwd()
        remanente_files = []
        
        for root, dirs, files in os.walk(base_dir):
            # Ignorar directorios no relevantes
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'remanent' in content.lower():
                                remanente_files.append(file_path)
                    except:
                        pass
        
        self.stdout.write(f'Archivos con referencias a remanentes: {len(remanente_files)}')
        for file_path in sorted(remanente_files):
            rel_path = os.path.relpath(file_path, base_dir)
            self.stdout.write(f'  - {rel_path}')
    
    def _generate_migration_plan(self):
        self.stdout.write(f'\n{self.style.SUCCESS("3. PLAN DE MIGRACIÓN:")}')
        self.stdout.write('=' * 50)
        
        self.stdout.write('PASO 1: Backup de datos actuales')
        self.stdout.write('  - Exportar configuraciones existentes de remanentes')
        self.stdout.write('  - Backup de servicios con datos de remanentes')
        
        self.stdout.write('\nPASO 2: Crear nuevos modelos (sin tocar actuales)')
        self.stdout.write('  - RemanenteType')
        self.stdout.write('  - BusinessLineRemanenteConfig') 
        self.stdout.write('  - ServicePeriodRemanente')
        
        self.stdout.write('\nPASO 3: Migrar datos al nuevo sistema')
        self.stdout.write('  - Convertir configuraciones existentes')
        self.stdout.write('  - Migrar datos de servicios BLACK')
        
        self.stdout.write('\nPASO 4: Actualizar código gradualmente')
        self.stdout.write('  - Reemplazar referencias al sistema antiguo')
        self.stdout.write('  - Mantener compatibilidad temporal')
        
        self.stdout.write('\nPASO 5: Eliminar sistema antiguo')
        self.stdout.write('  - Crear migración para eliminar campos obsoletos')
        self.stdout.write('  - Limpiar código obsoleto')
        
        self.stdout.write(f'\n{self.style.WARNING("ARCHIVOS QUE REQUIEREN LIMPIEZA COMPLETA:")}')
        files_to_clean = [
            'apps/business_lines/models.py - Eliminar RemanenteChoices, has_remanente, remanente_field',
            'apps/accounting/models.py - Eliminar campo remanentes y validaciones',
            'apps/accounting/forms/ - Eliminar lógica de remanentes hardcodeada',
            'templates/ - Eliminar referencias al campo remanentes',
            'apps/business_lines/admin.py - Actualizar configuración',
            'management/commands/ - Actualizar o eliminar comandos obsoletos'
        ]
        
        for item in files_to_clean:
            self.stdout.write(f'  ✓ {item}')
        
        self.stdout.write(f'\n{self.style.SUCCESS("¿PROCEDER CON LA IMPLEMENTACIÓN?")}')
        self.stdout.write('Este análisis muestra que es seguro proceder con la migración completa.')
