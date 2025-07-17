from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Load all fixtures for the Zento ERP and set up test users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset database before loading fixtures',
        )

    def handle(self, *args, **options):
        if options.get('reset', False):
            self.stdout.write('Resetting database...')
            call_command('flush', '--noinput')
            call_command('migrate')

        self.stdout.write(self.style.SUCCESS('Loading fixtures for Zento ERP...'))
        
        fixtures = [
            ('apps/business_lines/fixtures/business_lines_complete.json', 'Business Lines'),
            ('apps/authentication/fixtures/users.json', 'Users'),
            ('apps/expenses/fixtures/categories_complete.json', 'Expense Categories'),
            ('apps/accounting/fixtures/clients.json', 'Clients'),
            ('apps/accounting/fixtures/client_services.json', 'Client Services'),
            ('apps/expenses/fixtures/expenses.json', 'Expenses'),
        ]

        with transaction.atomic():
            for fixture_path, description in fixtures:
                try:
                    call_command('loaddata', fixture_path)
                    self.stdout.write(self.style.SUCCESS(f'✓ {description} loaded'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ Error loading {description}: {str(e)}'))
                    raise

        self.stdout.write('Setting up user passwords...')
        try:
            admin_user = User.objects.get(username='admin')
            admin_user.set_password('admin123')
            admin_user.save()
            
            maria_user = User.objects.get(username='maria.glow')
            maria_user.set_password('maria123')
            maria_user.save()
            
            carlos_user = User.objects.get(username='carlos.glow')
            carlos_user.set_password('carlos123')
            carlos_user.save()
            
            self.stdout.write(self.style.SUCCESS('✓ User passwords set'))
        except User.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'✗ Error setting passwords: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('\n=== FIXTURE LOADING COMPLETE ==='))
        
        from apps.business_lines.models import BusinessLine
        from apps.accounting.models import Client, ClientService
        from apps.expenses.models import ExpenseCategory, Expense
        
        self.stdout.write(f'Users: {User.objects.count()}')
        self.stdout.write(f'Business lines: {BusinessLine.objects.count()}')
        self.stdout.write(f'Clients: {Client.objects.count()}')
        self.stdout.write(f'Client services: {ClientService.objects.count()}')
        self.stdout.write(f'Expense categories: {ExpenseCategory.objects.count()}')
        self.stdout.write(f'Expenses: {Expense.objects.count()}')
        
        self.stdout.write('\n=== TEST USERS ===')
        self.stdout.write('Admin: username=admin, password=admin123')
        self.stdout.write('María (Glow Viewer): username=maria.glow, password=maria123')
        self.stdout.write('Carlos (Glow Viewer): username=carlos.glow, password=carlos123')
        
        self.stdout.write(self.style.SUCCESS('\nAll fixtures loaded successfully! 🎉'))
