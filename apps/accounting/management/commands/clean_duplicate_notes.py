from django.core.management.base import BaseCommand
from django.db import transaction

from ...models import ClientService
from ...services.notes_manager import ServiceNotesManager


class Command(BaseCommand):
    help = 'Limpia notas duplicadas en los servicios de clientes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin aplicar los cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Modo DRY RUN - No se aplicarán cambios')
            )
        
        services_updated = 0
        services_with_changes = []
        
        for service in ClientService.objects.filter(notes__isnull=False).exclude(notes=''):
            original_notes = service.notes
            cleaned_notes = ServiceNotesManager.clean_notes(original_notes)
            
            if original_notes != cleaned_notes:
                services_with_changes.append({
                    'id': service.id,
                    'client': str(service.client),
                    'original': original_notes,
                    'cleaned': cleaned_notes
                })
                
                if not dry_run:
                    with transaction.atomic():
                        service.notes = cleaned_notes
                        service.save(update_fields=['notes', 'modified'])
                
                services_updated += 1
        
        if dry_run:
            self.stdout.write(f"\nSe encontraron {services_updated} servicios con notas que necesitan limpieza:")
            for service_info in services_with_changes:
                self.stdout.write(
                    f"\nServicio {service_info['id']} - {service_info['client']}"
                )
                self.stdout.write(f"  Original: {service_info['original']}")
                self.stdout.write(f"  Limpiado: {service_info['cleaned']}")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Se limpiaron las notas de {services_updated} servicios'
                )
            )
        
        if not services_updated:
            self.stdout.write(
                self.style.SUCCESS('No se encontraron servicios con notas duplicadas')
            )
