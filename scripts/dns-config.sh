#!/bin/bash

# =============================================================================
# dns-config.sh - Configuración DNS para zentoerp.com
# =============================================================================
# Este script proporciona las configuraciones DNS necesarias para
# configurar correctamente los subdominios multi-tenant

set -e

echo "🌐 Configuración DNS para zentoerp.com"
echo "======================================"

echo ""
echo "📋 CONFIGURACIÓN DNS REQUERIDA:"
echo "-------------------------------"

echo ""
echo "1. 📍 DOMINIO PRINCIPAL (zentoerp.com):"
echo "   Tipo: A"
echo "   Nombre: @"
echo "   Valor: [IP_DE_RENDER] (se obtiene automáticamente)"
echo "   TTL: 300"

echo ""
echo "2. 🔄 SUBDOMINIO WWW (www.zentoerp.com):"
echo "   Tipo: CNAME"
echo "   Nombre: www"
echo "   Valor: zentoerp.com"
echo "   TTL: 300"

echo ""
echo "3. 🏢 SUBDOMINIOS MULTI-TENANT (*.zentoerp.com):"
echo "   Tipo: CNAME"
echo "   Nombre: *"
echo "   Valor: zentoerp.com"
echo "   TTL: 300"

echo ""
echo "4. 📧 CONFIGURACIÓN DE EMAIL (MX Records):"
echo "   Tipo: MX"
echo "   Nombre: @"
echo "   Valor: [SERVIDOR_EMAIL] (ej: mx.google.com)"
echo "   Prioridad: 10"
echo "   TTL: 3600"

echo ""
echo "5. 🔒 CONFIGURACIÓN SSL/TLS:"
echo "   - Render maneja automáticamente SSL para dominio principal"
echo "   - Wildcard SSL incluido para subdominios *.zentoerp.com"
echo "   - Certificados Let's Encrypt renovados automáticamente"

echo ""
echo "📝 EJEMPLOS DE SUBDOMINIOS MULTI-TENANT:"
echo "---------------------------------------"
echo "• nutricion.zentoerp.com    (Tenant: nutricion)"
echo "• consultorio.zentoerp.com  (Tenant: consultorio)"
echo "• clinica.zentoerp.com      (Tenant: clinica)"
echo "• empresa.zentoerp.com      (Tenant: empresa)"

echo ""
echo "⚙️  CONFIGURACIÓN EN RENDER:"
echo "----------------------------"
echo "1. Agregar dominio personalizado: zentoerp.com"
echo "2. Agregar wildcard domain: *.zentoerp.com"
echo "3. Verificar configuración DNS"
echo "4. Activar SSL automático"

echo ""
echo "🔧 COMANDOS ÚTILES PARA VERIFICAR DNS:"
echo "--------------------------------------"
echo "• dig zentoerp.com"
echo "• dig www.zentoerp.com"
echo "• dig nutricion.zentoerp.com"
echo "• nslookup zentoerp.com"

echo ""
echo "✅ CHECKLIST DE CONFIGURACIÓN:"
echo "------------------------------"
echo "□ Dominio principal configurado"
echo "□ Wildcard subdomain configurado"
echo "□ SSL/TLS activado"
echo "□ MX records configurados (si se usa email)"
echo "□ Verificación DNS completada"
echo "□ Pruebas de subdominios funcionando"

echo ""
echo "🚨 IMPORTANTE:"
echo "-------------"
echo "• Los cambios DNS pueden tardar 24-48 horas en propagarse"
echo "• Usar herramientas como https://whatsmydns.net/ para verificar"
echo "• Configurar primero en un subdominio de prueba si es necesario"

echo ""
echo "📚 DOCUMENTACIÓN:"
echo "----------------"
echo "• Render Custom Domains: https://render.com/docs/custom-domains"
echo "• Django-tenants: https://django-tenants.readthedocs.io/"
echo "• SSL Configuration: https://render.com/docs/ssl"

echo ""
echo "🎯 SIGUIENTE PASO: Configurar variables de entorno en Render"
echo "============================================================"
