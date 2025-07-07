from django.core.management.base import BaseCommand
from apps.tenants.models import Tenant, Domain
import platform


class Command(BaseCommand):
    help = 'Muestra las configuraciones necesarias para desarrollo local'

    def handle(self, *args, **options):
        system = platform.system()
        
        self.stdout.write(
            self.style.SUCCESS('=== CONFIGURACIÓN PARA DESARROLLO LOCAL ===\n')
        )
        
        # Obtener todos los dominios excepto el público
        domains = Domain.objects.exclude(tenant__schema_name='public')
        
        if not domains.exists():
            self.stdout.write(
                self.style.WARNING('No hay dominios de tenants configurados.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING('Para que los subdominios funcionen localmente, necesitas:')
        )
        
        if system == 'Darwin':  # macOS
            self.stdout.write('\n1. Agregar estas líneas al archivo /etc/hosts:')
            self.stdout.write('   sudo nano /etc/hosts\n')
            
            for domain in domains:
                domain_name = domain.domain.replace(':8000', '')
                self.stdout.write(f'   127.0.0.1    {domain_name}')
            
            self.stdout.write('\n2. O usar dnsmasq para manejar todos los subdominios:')
            self.stdout.write('   brew install dnsmasq')
            self.stdout.write('   echo "address=/.localhost/127.0.0.1" >> /usr/local/etc/dnsmasq.conf')
            self.stdout.write('   sudo brew services start dnsmasq')
            
        elif system == 'Linux':
            self.stdout.write('\n1. Agregar estas líneas al archivo /etc/hosts:')
            self.stdout.write('   sudo nano /etc/hosts\n')
            
            for domain in domains:
                domain_name = domain.domain.replace(':8000', '')
                self.stdout.write(f'   127.0.0.1    {domain_name}')
                
        elif system == 'Windows':
            self.stdout.write('\n1. Agregar estas líneas al archivo C:\\Windows\\System32\\drivers\\etc\\hosts:')
            self.stdout.write('   (Ejecutar como administrador)\n')
            
            for domain in domains:
                domain_name = domain.domain.replace(':8000', '')
                self.stdout.write(f'   127.0.0.1    {domain_name}')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('URLs DISPONIBLES:'))
        self.stdout.write('='*50)
        
        # Tenant público
        public_domain = Domain.objects.filter(tenant__schema_name='public').first()
        if public_domain:
            self.stdout.write(f'🏠 Página principal: http://{public_domain.domain}')
            self.stdout.write(f'👤 Admin: http://{public_domain.domain}/admin')
        
        self.stdout.write('\n📋 TENANTS DE NUTRICIONISTAS:')
        for domain in domains:
            tenant = domain.tenant
            self.stdout.write(
                f'   {tenant.name}: http://{domain.domain}'
            )
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.WARNING('ALTERNATIVA SIN CONFIGURAR /etc/hosts:'))
        self.stdout.write('='*50)
        self.stdout.write('Si no quieres modificar /etc/hosts, puedes:')
        self.stdout.write('1. Acceder siempre desde: http://localhost:8000')
        self.stdout.write('2. El sistema te redirigirá automáticamente al tenant correcto')
        self.stdout.write('3. Solo necesitas las credenciales del nutricionista')
        
        self.stdout.write('\n' + self.style.SUCCESS('¡El servidor está listo!'))
        self.stdout.write('Servidor corriendo en: http://0.0.0.0:8000')
