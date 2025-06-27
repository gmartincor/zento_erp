from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounting.models import Client
from apps.accounting.services.client_state_manager import ClientStateManager


class Command(BaseCommand):
    help = 'Sincroniza estados de clientes con sus servicios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin realizar cambios reales',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Modo DRY RUN - No se realizarán cambios'))
        
        inactive_clients = Client.objects.filter(is_active=False)
        self.stdout.write(f'Encontrados {inactive_clients.count()} clientes inactivos')
        
        for client in inactive_clients:
            active_services = client.services.filter(is_active=True)
            
            if active_services.exists():
                self.stdout.write(f'Cliente {client.full_name} (ID: {client.id}) tiene {active_services.count()} servicios activos')
                
                if not dry_run:
                    result = ClientStateManager.deactivate_client(client)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Desactivados {result["total_services_affected"]} servicios para cliente {client.full_name}'
                        )
                    )
                else:
                    self.stdout.write(f'[DRY RUN] Se desactivarían {active_services.count()} servicios')
        
        active_clients = Client.objects.filter(is_active=True)
        self.stdout.write(f'Verificando {active_clients.count()} clientes activos')
        
        for client in active_clients:
            inactive_services = client.services.filter(is_active=False)
            
            if inactive_services.exists():
                self.stdout.write(f'Cliente activo {client.full_name} (ID: {client.id}) tiene {inactive_services.count()} servicios inactivos')
                
                if not dry_run:
                    result = ClientStateManager.reactivate_client(client)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Reactivados {result["total_services_affected"]} servicios para cliente {client.full_name}'
                        )
                    )
                else:
                    self.stdout.write(f'[DRY RUN] Se reactivarían {inactive_services.count()} servicios')
        
        self.stdout.write(self.style.SUCCESS('Sincronización completada'))
