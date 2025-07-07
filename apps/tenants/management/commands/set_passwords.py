from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from apps.authentication.models import User


class Command(BaseCommand):
    help = 'Establece contraseñas para usuarios de prueba'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nombre de usuario específico (opcional)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='test123',
            help='Contraseña a establecer (default: test123)'
        )

    def handle(self, *args, **options):
        username = options.get('username')
        password = options.get('password')
        
        if username:
            # Establecer contraseña para un usuario específico
            try:
                user = User.objects.get(username=username)
                user.set_password(password)
                user.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Contraseña establecida para {username}')
                )
                self.stdout.write(f'   Username: {username}')
                self.stdout.write(f'   Password: {password}')
                if user.tenant:
                    self.stdout.write(f'   Tenant: {user.tenant.name}')
                
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Usuario {username} no encontrado')
                )
        else:
            # Establecer contraseña para todos los usuarios de tenants
            users = User.objects.filter(tenant__isnull=False, is_active=True)
            
            if not users.exists():
                self.stdout.write(
                    self.style.WARNING('No hay usuarios de tenants para actualizar')
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS('=== ESTABLECIENDO CONTRASEÑAS ===\n')
            )
            
            for user in users:
                user.set_password(password)
                user.save()
                
                self.stdout.write(f'✅ {user.username}')
                self.stdout.write(f'   Nombre: {user.get_full_name() or "Sin nombre"}')
                self.stdout.write(f'   Password: {password}')
                self.stdout.write(f'   Tenant: {user.tenant.name}')
                self.stdout.write('')
            
            self.stdout.write(
                self.style.SUCCESS(f'🎉 Contraseñas establecidas para {users.count()} usuarios')
            )
            self.stdout.write(
                self.style.WARNING(f'Contraseña común: {password}')
            )
