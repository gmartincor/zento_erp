#!/usr/bin/env python
"""
Script para actualizar dominios primarios a versiones RFC-compliant
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.tenants.models import Domain, Tenant

def update_primary_domains():
    print("=== Actualizando Dominios Primarios a RFC-Compliant ===")
    
    # Mapeo de dominios inválidos a válidos
    domain_mappings = {
        'tenant_laura.localhost': 'tenant-laura.localhost',
        'tenant_roberto.localhost': 'tenant-roberto.localhost', 
        'tenant_roberto2.localhost': 'tenant-roberto2.localhost',
        'tenant_test.localhost': 'tenant-test.localhost',
        'ana_martinez.localhost': 'ana-martinez.localhost',
    }
    
    for old_domain, new_domain in domain_mappings.items():
        try:
            # Buscar el dominio primario actual
            old_domain_obj = Domain.objects.filter(domain=old_domain, is_primary=True).first()
            if old_domain_obj:
                tenant = old_domain_obj.tenant
                
                # Verificar si ya existe el dominio válido
                new_domain_obj = Domain.objects.filter(domain=new_domain).first()
                if new_domain_obj:
                    # Hacer el dominio válido como primario
                    new_domain_obj.is_primary = True
                    new_domain_obj.save()
                    print(f"✅ Actualizado primario: {new_domain} para tenant {tenant.schema_name}")
                    
                    # Hacer el dominio inválido como secundario
                    old_domain_obj.is_primary = False
                    old_domain_obj.save()
                    print(f"   ⬇️  Degradado a secundario: {old_domain}")
                else:
                    print(f"❌ No existe dominio válido {new_domain} para actualizar")
            else:
                print(f"⚠️  No encontrado dominio primario: {old_domain}")
                
        except Exception as e:
            print(f"❌ Error actualizando {old_domain}: {e}")
    
    # Verificar estado final
    print("\n=== Estado Final de Dominios Primarios ===")
    primary_domains = Domain.objects.filter(is_primary=True)
    for domain in primary_domains:
        status = "✅ VÁLIDO" if '_' not in domain.domain else "❌ INVÁLIDO"
        print(f"{status}: {domain.domain} -> {domain.tenant.schema_name}")

if __name__ == "__main__":
    update_primary_domains()
