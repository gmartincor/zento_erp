from django.core.management.base import BaseCommand
from django.db import transaction
from apps.business_lines.models import BusinessLine
from apps.accounting.models import ClientService


class Command(BaseCommand):
    help = 'Diagnostica y corrige problemas de configuración de remanentes en líneas de negocio'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Aplicar correcciones automáticas a los problemas encontrados',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué cambios se harían sin aplicarlos',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== DIAGNÓSTICO DE REMANENTES EN LÍNEAS DE NEGOCIO ===\n'))
        
        problems_found = []
        
        # 1. Buscar líneas de negocio con has_remanente=True pero remanente_field=None
        invalid_bl = BusinessLine.objects.filter(has_remanente=True, remanente_field__isnull=True)
        
        if invalid_bl.exists():
            self.stdout.write(self.style.ERROR('PROBLEMA 1: Líneas de negocio con remanente habilitado pero sin tipo configurado:'))
            for bl in invalid_bl:
                self.stdout.write(f'  - ID: {bl.id}, Nombre: "{bl.name}", Nivel: {bl.level}')
                problems_found.append(('invalid_remanente_config', bl))
            self.stdout.write('')
        
        # 2. Buscar servicios BUSINESS que usan líneas de negocio problemáticas
        problematic_services = ClientService.objects.filter(
            category=ClientService.CategoryChoices.BUSINESS,
            business_line__in=invalid_bl
        )
        
        if problematic_services.exists():
            self.stdout.write(self.style.ERROR('PROBLEMA 2: Servicios BUSINESS que usan líneas de negocio problemáticas:'))
            for service in problematic_services:
                self.stdout.write(f'  - Servicio ID: {service.id}, Cliente: {service.client.full_name}, '
                                f'Línea: "{service.business_line.name}"')
                problems_found.append(('problematic_service', service))
            self.stdout.write('')
        
        # 3. Verificar líneas de negocio que deberían tener remanente según su nombre
        all_bl = BusinessLine.objects.all()
        missing_remanente_config = []
        
        for bl in all_bl:
            name_lower = bl.name.lower()
            expected_remanente = None
            should_have_remanente = False
            
            if "pepe-normal" in name_lower:
                expected_remanente = BusinessLine.RemanenteChoices.REMANENTE_PEPE
                should_have_remanente = True
            elif "pepe-videocall" in name_lower:
                expected_remanente = BusinessLine.RemanenteChoices.REMANENTE_PEPE_VIDEO
                should_have_remanente = True
            elif "dani-rubi" in name_lower:
                expected_remanente = BusinessLine.RemanenteChoices.REMANENTE_DANI
                should_have_remanente = True
            elif "dani" in name_lower and "rubi" not in name_lower:
                expected_remanente = BusinessLine.RemanenteChoices.REMANENTE_AVEN
                should_have_remanente = True
            
            if should_have_remanente:
                if not bl.has_remanente or bl.remanente_field != expected_remanente:
                    missing_remanente_config.append((bl, expected_remanente))
                    problems_found.append(('missing_expected_remanente', bl, expected_remanente))
        
        if missing_remanente_config:
            self.stdout.write(self.style.WARNING('PROBLEMA 3: Líneas de negocio que deberían tener remanente según su nombre:'))
            for bl, expected in missing_remanente_config:
                current_config = f"has_remanente={bl.has_remanente}, remanente_field={bl.remanente_field}"
                self.stdout.write(f'  - ID: {bl.id}, Nombre: "{bl.name}"')
                self.stdout.write(f'    Configuración actual: {current_config}')
                self.stdout.write(f'    Configuración esperada: has_remanente=True, remanente_field={expected}')
            self.stdout.write('')
        
        # 4. Mostrar resumen
        if not problems_found:
            self.stdout.write(self.style.SUCCESS('✅ No se encontraron problemas de configuración de remanentes.'))
            return
        
        self.stdout.write(self.style.WARNING(f'RESUMEN: Se encontraron {len(problems_found)} problemas.'))
        
        # 5. Aplicar correcciones si se solicita
        if options['fix'] and not options['dry_run']:
            self.stdout.write(self.style.WARNING('\n=== APLICANDO CORRECCIONES ==='))
            self._apply_fixes(problems_found)
        elif options['dry_run'] or not options['fix']:
            self.stdout.write(self.style.INFO('\n=== CORRECCIONES PROPUESTAS ==='))
            self._show_proposed_fixes(problems_found, dry_run=options['dry_run'])
    
    def _show_proposed_fixes(self, problems, dry_run=False):
        action_word = "Se aplicarían" if dry_run else "Para aplicar correcciones, ejecute"
        
        self.stdout.write(f'{action_word} las siguientes acciones:')
        
        for problem_type, *args in problems:
            if problem_type == 'invalid_remanente_config':
                bl = args[0]
                self.stdout.write(f'  - Desactivar remanente en línea de negocio "{bl.name}" (ID: {bl.id})')
            
            elif problem_type == 'missing_expected_remanente':
                bl, expected = args[0], args[1]
                self.stdout.write(f'  - Configurar línea de negocio "{bl.name}" (ID: {bl.id}):')
                self.stdout.write(f'    has_remanente=True, remanente_field={expected}')
        
        if not dry_run:
            self.stdout.write(f'\n{self.style.SUCCESS("python manage.py fix_remanentes --fix")}')
    
    @transaction.atomic
    def _apply_fixes(self, problems):
        fixes_applied = 0
        
        for problem_type, *args in problems:
            try:
                if problem_type == 'invalid_remanente_config':
                    bl = args[0]
                    bl.has_remanente = False
                    bl.remanente_field = None
                    bl.save()
                    self.stdout.write(self.style.SUCCESS(f'✅ Desactivado remanente en "{bl.name}"'))
                    fixes_applied += 1
                
                elif problem_type == 'missing_expected_remanente':
                    bl, expected = args[0], args[1]
                    bl.has_remanente = True
                    bl.remanente_field = expected
                    bl.save()
                    self.stdout.write(self.style.SUCCESS(f'✅ Configurado remanente en "{bl.name}": {expected}'))
                    fixes_applied += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error al aplicar corrección: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 Se aplicaron {fixes_applied} correcciones exitosamente.'))
        
        if fixes_applied > 0:
            self.stdout.write(self.style.WARNING('\nIMPORTANTE: Verifique que los servicios BUSINESS existentes '
                                               'sigan funcionando correctamente después de estos cambios.'))
