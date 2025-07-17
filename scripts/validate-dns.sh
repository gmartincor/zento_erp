#!/bin/bash

# =============================================================================
# validate-dns.sh - Validación de configuración DNS para zentoerp.com
# =============================================================================
# Este script valida que la configuración DNS esté correcta antes del deploy

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
DOMAIN="zentoerp.com"
SUBDOMAINS=("www" "nutricion" "consultorio" "clinica" "empresa")

echo -e "${BLUE}🔍 Validando configuración DNS para ${DOMAIN}${NC}"
echo "================================================="

# Función para validar DNS
validate_dns() {
    local domain=$1
    local record_type=$2
    
    echo -n "Validando ${record_type} para ${domain}... "
    
    if command -v dig &> /dev/null; then
        result=$(dig +short ${record_type} ${domain} 2>/dev/null)
    elif command -v nslookup &> /dev/null; then
        result=$(nslookup ${domain} 2>/dev/null | grep "Address:" | tail -1 | awk '{print $2}')
    else
        echo -e "${RED}❌ No se encontró dig ni nslookup${NC}"
        return 1
    fi
    
    if [ -n "$result" ]; then
        echo -e "${GREEN}✅ ${result}${NC}"
        return 0
    else
        echo -e "${RED}❌ No resuelve${NC}"
        return 1
    fi
}

# Función para validar SSL
validate_ssl() {
    local domain=$1
    echo -n "Validando SSL para ${domain}... "
    
    if command -v openssl &> /dev/null; then
        if openssl s_client -connect ${domain}:443 -servername ${domain} </dev/null 2>/dev/null | grep -q "Verify return code: 0"; then
            echo -e "${GREEN}✅ SSL válido${NC}"
            return 0
        else
            echo -e "${RED}❌ SSL inválido${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  openssl no disponible${NC}"
        return 1
    fi
}

# Función para validar respuesta HTTP
validate_http() {
    local domain=$1
    local protocol=$2
    echo -n "Validando HTTP${protocol^^} para ${domain}... "
    
    if command -v curl &> /dev/null; then
        if curl -s -I --max-time 10 "${protocol}://${domain}" | head -1 | grep -q "200\|301\|302"; then
            echo -e "${GREEN}✅ Responde correctamente${NC}"
            return 0
        else
            echo -e "${RED}❌ No responde${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  curl no disponible${NC}"
        return 1
    fi
}

# Validaciones principales
echo -e "\n${BLUE}📍 VALIDANDO DOMINIO PRINCIPAL${NC}"
echo "------------------------------"
validate_dns $DOMAIN "A"
validate_ssl $DOMAIN
validate_http $DOMAIN "https"

echo -e "\n${BLUE}🔄 VALIDANDO SUBDOMINIOS${NC}"
echo "-------------------------"
for subdomain in "${SUBDOMAINS[@]}"; do
    full_domain="${subdomain}.${DOMAIN}"
    validate_dns $full_domain "CNAME"
    validate_ssl $full_domain
    validate_http $full_domain "https"
done

echo -e "\n${BLUE}📧 VALIDANDO CONFIGURACIÓN DE EMAIL${NC}"
echo "-----------------------------------"
validate_dns $DOMAIN "MX"

echo -e "\n${BLUE}🔍 INFORMACIÓN ADICIONAL${NC}"
echo "-------------------------"
echo "Propagación DNS mundial: https://whatsmydns.net/#A/${DOMAIN}"
echo "SSL Labs Test: https://www.ssllabs.com/ssltest/analyze.html?d=${DOMAIN}"
echo "DNS Checker: https://dnschecker.org/#A/${DOMAIN}"

echo -e "\n${BLUE}⚙️  COMANDOS ÚTILES${NC}"
echo "-------------------"
echo "• dig ${DOMAIN}"
echo "• dig www.${DOMAIN}"
echo "• dig *.${DOMAIN}"
echo "• nslookup ${DOMAIN}"
echo "• curl -I https://${DOMAIN}"

echo -e "\n${GREEN}✅ Validación DNS completada${NC}"
echo "=========================="

# Verificar si todo está correcto
if validate_dns $DOMAIN "A" && validate_ssl $DOMAIN; then
    echo -e "\n${GREEN}🎉 ¡Configuración DNS lista para producción!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Hay problemas con la configuración DNS${NC}"
    echo "Revisa los errores anteriores antes de hacer deploy"
    exit 1
fi
