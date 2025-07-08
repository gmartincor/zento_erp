#!/usr/bin/env python
"""
Script para verificar y actualizar dominios de tenants para usar nombres válidos RFC-compliant
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.tenants.models import Domain, Tenant

def check_and_update_domains():
    print("=== Revisión de Dominios Actuales ===")
    domains = Domain.objects.all()
    
    for domain in domains:
        print(f"- {domain.domain} (tenant: {domain.tenant.schema_name})")
        
        # Verificar si el dominio tiene guión bajo
        if '_' in domain.domain:
            new_domain = domain.domain.replace('_', '-')
            print(f"  ⚠️  Dominio inválido (contiene _): {domain.domain}")
            print(f"  ✅ Sugiriendo cambio a: {new_domain}")
            
            # Verificar si el nuevo dominio ya existe
            if Domain.objects.filter(domain=new_domain).exists():
                print(f"  ❌ El dominio {new_domain} ya existe")
            else:
                print(f"  🔄 ¿Actualizar {domain.domain} -> {new_domain}? (s/n)")
                # En un script más complejo, podrías pedir confirmación del usuario
                # Por ahora solo mostramos lo que haríamos
                
    print("\n=== Análisis de Problemas RFC ===")
    invalid_domains = Domain.objects.filter(domain__contains='_')
    if invalid_domains:
        print(f"Encontrados {invalid_domains.count()} dominios inválidos con guión bajo:")
        for domain in invalid_domains:
            print(f"  - {domain.domain}")
    else:
        print("✅ Todos los dominios son válidos según RFC 1034/1035")

def create_valid_domain_mappings():
    """Crear dominios válidos para testing"""
    mappings = {
        'tenant_laura.localhost': 'tenant-laura.localhost',
        'tenant_roberto.localhost': 'tenant-roberto.localhost',
        'tenant_roberto2.localhost': 'tenant-roberto2.localhost',
        'tenant_test.localhost': 'tenant-test.localhost',
        'ana_martinez.localhost': 'ana-martinez.localhost',
    }
    
    print("\n=== Creando Dominios Válidos para Testing ===")
    for old_domain, new_domain in mappings.items():
        try:
            # Buscar el dominio con guión bajo
            old_domain_obj = Domain.objects.filter(domain=old_domain).first()
            if old_domain_obj:
                # Verificar si el nuevo dominio ya existe
                if not Domain.objects.filter(domain=new_domain).exists():
                    # Crear nuevo dominio válido
                    new_domain_obj = Domain.objects.create(
                        domain=new_domain,
                        tenant=old_domain_obj.tenant,
                        is_primary=False  # Mantener el original como primario por ahora
                    )
                    print(f"✅ Creado: {new_domain} -> {old_domain_obj.tenant.schema_name}")
                else:
                    print(f"⚠️  Ya existe: {new_domain}")
            else:
                print(f"❌ No encontrado dominio original: {old_domain}")
        except Exception as e:
            print(f"❌ Error creando {new_domain}: {e}")

if __name__ == "__main__":
    check_and_update_domains()
    print("\n" + "="*50)
    create_valid_domain_mappings()
    print("\n" + "="*50)
    print("Script completado. Revisa los dominios y actualiza /etc/hosts si es necesario.")
