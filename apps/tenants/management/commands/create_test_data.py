from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant, Domain

User = get_user_model()


class Command(BaseCommand):
    help = 'Crear datos de prueba para desarrollo'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Crear tenant de prueba
                tenant, created = Tenant.objects.get_or_create(
                    schema_name='nutricionista1',
                    defaults={
                        'name': 'Dr. María García',
                        'email': 'maria@nutricion.com',
                        'status': Tenant.StatusChoices.ACTIVE,
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Tenant creado: {tenant.name}')
                    )
                
                # Crear dominio
                domain, domain_created = Domain.objects.get_or_create(
                    domain='nutricionista1.localhost:8000',
                    defaults={
                        'tenant': tenant,
                        'is_primary': True
                    }
                )
                
                if domain_created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Dominio creado: {domain.domain}')
                    )
                
                # Crear usuario asociado
                user, user_created = User.objects.get_or_create(
                    username='maria',
                    defaults={
                        'email': 'maria@nutricion.com',
                        'first_name': 'María',
                        'last_name': 'García',
                        'tenant': tenant
                    }
                )
                
                if user_created:
                    user.set_password('123456')
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Usuario creado: {user.username}')
                    )
                elif not user.tenant:
                    user.tenant = tenant
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Usuario asociado al tenant: {user.username}')
                    )
                
                self.stdout.write(
                    self.style.SUCCESS('\n--- DATOS DE PRUEBA ---')
                )
                self.stdout.write(f'URL: http://nutricionista1.localhost:8000/')
                self.stdout.write(f'Usuario: maria')
                self.stdout.write(f'Contraseña: 123456')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creando datos de prueba: {str(e)}')
            )
