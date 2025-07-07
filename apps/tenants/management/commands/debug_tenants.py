from django.core.management.base import BaseCommand
from django_tenants.utils import tenant_context, connection
from apps.tenants.models import Tenant, Domain


class Command(BaseCommand):
    help = 'Debug de configuración de tenants y dominios'

    def handle(self, *args, **options):
        self.stdout.write("🔍 VERIFICACIÓN DE CONFIGURACIÓN DE TENANTS\n")
        
        # Verificar configuración básica
        self.stdout.write("📋 CONFIGURACIÓN BÁSICA:")
        self.stdout.write(f"   Current schema: {connection.schema_name}")
        self.stdout.write(f"   Current tenant: {connection.tenant}")
        
        # Listar todos los tenants
        self.stdout.write("\n📁 TODOS LOS TENANTS:")
        tenants = Tenant.objects.all()
        for tenant in tenants:
            self.stdout.write(f"   - {tenant.name}")
            self.stdout.write(f"     Schema: {tenant.schema_name}")
            self.stdout.write(f"     Status: {tenant.status}")
            self.stdout.write(f"     Active: {tenant.is_active}")
            
            # Listar dominios de cada tenant
            domains = Domain.objects.filter(tenant=tenant)
            if domains:
                self.stdout.write(f"     Dominios:")
                for domain in domains:
                    self.stdout.write(f"       • {domain.domain} (primario: {domain.is_primary})")
            else:
                self.stdout.write(f"     ❌ Sin dominios configurados")
            self.stdout.write("")
        
        # Probar resolución de tenant por dominio
        self.stdout.write("\n🌐 PRUEBA DE RESOLUCIÓN DE DOMINIOS:")
        test_domains = [
            'localhost',
            'tenant_test.localhost',
            'ana-martinez.localhost',
            'carlos.localhost'
        ]
        
        for domain_name in test_domains:
            try:
                domain = Domain.objects.filter(domain=domain_name).first()
                if domain:
                    self.stdout.write(f"   ✅ {domain_name} → {domain.tenant.name} ({domain.tenant.schema_name})")
                else:
                    self.stdout.write(f"   ❌ {domain_name} → No encontrado")
            except Exception as e:
                self.stdout.write(f"   💥 {domain_name} → Error: {str(e)}")
        
        self.stdout.write("\n✅ Verificación completada")
