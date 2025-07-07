from django.core.management.base import BaseCommand
from apps.authentication.models import User


class Command(BaseCommand):
    help = 'Establece contraseñas para usuarios de prueba'

    def handle(self, *args, **options):
        users_passwords = [
            ('ana', 'ana123'),
            ('carlos_carlos', 'carlos123'),
            ('maria_maria', 'maria123'),
            ('administrador', 'admin123'),
        ]
        
        for username, password in users_passwords:
            try:
                user = User.objects.get(username=username)
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Contraseña establecida para {username}: {password}')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Usuario {username} no encontrado')
                )
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Contraseñas de prueba establecidas')
        )
