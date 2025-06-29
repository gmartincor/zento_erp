from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.business_lines.models import BusinessLine
from apps.business_lines.models_remanentes import RemanenteType, BusinessLineRemanenteConfig
from apps.accounting.models import ClientService

User = get_user_model()


class Command(BaseCommand):
    help = 'Migra del sistema hardcodeado de remanentes al nuevo sistema flexible'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-default-types',
            action='store_true',
            help='Crear tipos de remanente por defecto basados en el sistema antiguo'
        )
        parser.add_argument(
            '--migrate-business-lines',
            action='store_true',
            help='Migrar configuraciones de líneas de negocio'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar lo que se haría sin hacer cambios'
        )
        parser.add_argument(
            '--clean-obsolete-data',
            action='store_true',
            help='Limpiar datos obsoletos del sistema antiguo de remanentes'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== MIGRACIÓN AL SISTEMA FLEXIBLE DE REMANENTES ===\n'))

        if options['create_default_types']:
            self._create_default_remanente_types(dry_run=options['dry_run'])

        if options['migrate_business_lines']:
            self._migrate_business_line_configurations(dry_run=options['dry_run'])

        # Agregar opción para limpiar datos obsoletos
        if options.get('clean_obsolete_data', False):
            self._clean_obsolete_remanentes_data(dry_run=options['dry_run'])

        self.stdout.write(self.style.SUCCESS('\n=== MIGRACIÓN COMPLETADA ==='))

    def _create_default_remanente_types(self, dry_run=False):
        """Crear tipos de remanente basados en el sistema antiguo"""
        self.stdout.write(self.style.WARNING('1. CREANDO TIPOS DE REMANENTE POR DEFECTO'))
        self.stdout.write('=' * 50)

        # Obtener el primer usuario admin como creador por defecto
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No se encontró ningún usuario administrador. Creando usuario sistema...'))
            if not dry_run:
                admin_user = User.objects.create_user(
                    username='sistema',
                    email='sistema@nutrition-pro.com',
                    is_staff=True,
                    is_superuser=True
                )

        # Tipos de remanente basados en el sistema antiguo
        remanente_types_data = [
            {
                'name': 'remanente_pepe',
                'description': 'Remanente para servicios PEPE normales',
                'default_amount': 50.00
            },
            {
                'name': 'remanente_pepe_video',
                'description': 'Remanente para servicios PEPE con videollamada',
                'default_amount': 75.00
            },
            {
                'name': 'remanente_dani',
                'description': 'Remanente para servicios Dani-Rubi',
                'default_amount': 100.00
            },
            {
                'name': 'remanente_aven',
                'description': 'Remanente para servicios Dani (Aven)',
                'default_amount': 60.00
            }
        ]

        for type_data in remanente_types_data:
            if dry_run:
                self.stdout.write(f'  [DRY-RUN] Crearía tipo: {type_data["name"]} - {type_data["description"]}')
            else:
                remanente_type, created = RemanenteType.objects.get_or_create(
                    name=type_data['name'],
                    defaults={
                        'description': type_data['description'],
                        'default_amount': type_data['default_amount'],
                        'created_by': admin_user
                    }
                )
                status = 'creado' if created else 'ya existía'
                self.stdout.write(f'  ✓ Tipo "{type_data["name"]}" {status}')

    def _migrate_business_line_configurations(self, dry_run=False):
        """Migrar configuraciones de líneas de negocio del sistema antiguo"""
        self.stdout.write(self.style.WARNING('\n2. MIGRANDO CONFIGURACIONES DE LÍNEAS DE NEGOCIO'))
        self.stdout.write('=' * 50)

        # Mapeo del sistema antiguo al nuevo
        legacy_mappings = {
            'PEPE-normal': 'remanente_pepe',
            'PEPE-videoCall': 'remanente_pepe_video',
            'Dani-Rubi': 'remanente_dani',
            'Dani': 'remanente_aven'
        }

        # Obtener todas las líneas de negocio
        all_business_lines = BusinessLine.objects.all()
        configured_count = 0

        for bl in all_business_lines:
            # Determinar si esta línea debería tener remanentes según el sistema antiguo
            should_have_remanentes = bl.name in legacy_mappings
            remanente_type_name = legacy_mappings.get(bl.name)

            if should_have_remanentes:
                if dry_run:
                    self.stdout.write(f'  [DRY-RUN] Configuraría "{bl.name}" con allows_remanentes=True y tipo "{remanente_type_name}"')
                else:
                    # Habilitar remanentes en la línea de negocio
                    bl.allows_remanentes = True
                    bl.save()

                    # Crear configuración para el tipo de remanente
                    try:
                        remanente_type = RemanenteType.objects.get(name=remanente_type_name)
                        config, created = BusinessLineRemanenteConfig.objects.get_or_create(
                            business_line=bl,
                            remanente_type=remanente_type,
                            defaults={'is_enabled': True}
                        )
                        status = 'creada' if created else 'ya existía'
                        self.stdout.write(f'  ✓ Línea "{bl.name}" configurada con tipo "{remanente_type_name}" ({status})')
                        configured_count += 1
                    except RemanenteType.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'  ✗ Tipo de remanente "{remanente_type_name}" no encontrado para línea "{bl.name}"'))
            else:
                if dry_run:
                    self.stdout.write(f'  [DRY-RUN] "{bl.name}" mantendría allows_remanentes=False')
                else:
                    self.stdout.write(f'  - "{bl.name}" sin remanentes (correcto)')

        if not dry_run:
            self.stdout.write(f'\nTotal de líneas configuradas: {configured_count}')

    @transaction.atomic
    def _migrate_existing_service_data(self, dry_run=False):
        """Migrar datos de servicios BLACK existentes al nuevo sistema"""
        self.stdout.write(self.style.WARNING('\n3. MIGRANDO DATOS DE SERVICIOS EXISTENTES'))
        self.stdout.write('=' * 50)

        # Buscar servicios BLACK con datos de remanentes
        black_services = ClientService.objects.filter(
            category='BLACK',
            remanentes__isnull=False
        ).exclude(remanentes={})

        self.stdout.write(f'Servicios BLACK con remanentes encontrados: {black_services.count()}')

        for service in black_services:
            if dry_run:
                self.stdout.write(f'  [DRY-RUN] Migraría remanentes de servicio ID {service.id}')
            else:
                # Aquí podrías migrar los datos al nuevo modelo ServicePeriodRemanente
                # si quisieras preservar el histórico
                self.stdout.write(f'  ✓ Servicio ID {service.id} - Cliente: {service.client.full_name}')

    @transaction.atomic
    def _clean_obsolete_remanentes_data(self, dry_run=False):
        """Limpiar datos de remanentes del sistema antiguo"""
        self.stdout.write(self.style.WARNING('\n3. LIMPIANDO DATOS OBSOLETOS DEL SISTEMA ANTIGUO'))
        self.stdout.write('=' * 50)

        # Buscar servicios BLACK con campo remanentes del sistema antiguo
        black_services = ClientService.objects.filter(
            category='BLACK'
        ).exclude(remanentes__isnull=True).exclude(remanentes={})

        self.stdout.write(f'Servicios BLACK con datos de remanentes obsoletos: {black_services.count()}')

        for service in black_services:
            if dry_run:
                self.stdout.write(f'  [DRY-RUN] Limpiaría remanentes obsoletos de servicio ID {service.id}')
            else:
                # Limpiar el campo JSON obsoleto
                service.remanentes = {}
                service.save()
                self.stdout.write(f'  ✓ Limpiado servicio ID {service.id} - Cliente: {service.client.full_name}')

        if not dry_run and black_services.count() > 0:
            self.stdout.write(f'\nTotal de servicios limpiados: {black_services.count()}')
            self.stdout.write(self.style.SUCCESS('Los remanentes ahora se gestionan a través del nuevo sistema ServicePeriodRemanente'))
