from django.core.management.base import BaseCommand
from apps.business_lines.models import BusinessLine
from apps.business_lines.services import BusinessLineService

class Command(BaseCommand):
    help = 'Actualiza el estado activo de todas las líneas de negocio basado en sus servicios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la ejecución sin realizar cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Ejecutando en modo simulación (dry-run)...'))
        else:
            self.stdout.write(self.style.WARNING('Actualizando estado de líneas de negocio...'))
        
        all_lines = BusinessLine.objects.all().order_by('level', 'name')
        updated_count = 0
        
        for line in all_lines:
            old_status = line.is_active
            
            has_active_services = BusinessLineService.check_line_has_active_services(line)
            has_active_sublines = BusinessLineService.check_line_has_active_sublines(line)
            new_status = has_active_services or has_active_sublines
            
            if old_status != new_status:
                self.stdout.write(
                    f'{"[DRY-RUN] " if dry_run else ""}Línea "{line.name}": '
                    f'{"Activa" if old_status else "Inactiva"} → '
                    f'{"Activa" if new_status else "Inactiva"}'
                )
                
                if not dry_run:
                    BusinessLine.objects.filter(pk=line.pk).update(is_active=new_status)
                    line.is_active = new_status
                
                updated_count += 1
        
        if updated_count == 0:
            self.stdout.write(self.style.SUCCESS('No se requirieron cambios.'))
        else:
            message = f'{updated_count} línea(s) {"serían actualizadas" if dry_run else "actualizadas"}.'
            self.stdout.write(self.style.SUCCESS(message))
