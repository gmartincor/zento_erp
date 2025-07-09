from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test users with correct passwords'

    def handle(self, *args, **options):
        # Delete existing users first
        User.objects.all().delete()
        
        # Create admin user
        admin = User.objects.create_user(
            username='admin',
            email='admin@nutricionpro.com',
            first_name='Admin',
            last_name='Principal',
            password='admin123'
        )
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        
        # Create maria.glow user
        maria = User.objects.create_user(
            username='maria.glow',
            email='maria.glow@nutricionpro.com',
            first_name='María',
            last_name='García',
            password='maria123',
            role='AUTONOMO'
        )
        
        # Create carlos.glow user
        carlos = User.objects.create_user(
            username='carlos.glow',
            email='carlos.glow@nutricionpro.com',
            first_name='Carlos',
            last_name='Martín',
            password='carlos123',
            role='AUTONOMO'
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created users:\n'
                f'- admin (password: admin123)\n'
                f'- maria.glow (password: maria123)\n'
                f'- carlos.glow (password: carlos123)'
            )
        )
