from django.core.management.base import BaseCommand
from apps.business_lines.services import BusinessLineService

class Command(BaseCommand):
    help = 'Actualiza el estado activo de todas las líneas de negocio basado en sus servicios'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando actualización del estado de líneas de negocio...'))
        
        BusinessLineService.update_all_business_lines_status()
        
        self.stdout.write(self.style.SUCCESS('Actualización del estado de líneas de negocio completada.'))
