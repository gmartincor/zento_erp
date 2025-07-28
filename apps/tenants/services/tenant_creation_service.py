from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import transaction
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant, Domain
from apps.authentication.models import User
import re


class TenantCreationService:
    
    @staticmethod
    def validate_schema_name(schema_name):
        schema_name = schema_name.lower().strip()
        
        if not re.match(r'^[a-z][a-z0-9_]*$', schema_name):
            raise ValidationError('Schema name debe empezar con letra y solo contener letras minúsculas, números y guiones bajos')
        
        if Tenant.objects.filter(schema_name=schema_name).exists():
            raise ValidationError(f'El schema name "{schema_name}" ya existe')
        
        return schema_name
    
    @staticmethod
    def validate_domain_name(domain_name):
        domain_name = domain_name.lower().strip()
        
        if not re.match(r'^[a-z0-9.-]+\.(zentoerp\.com|localhost)$', domain_name):
            raise ValidationError('Dominio debe ser un subdominio de zentoerp.com o localhost')
        
        if Domain.objects.filter(domain=domain_name).exists():
            raise ValidationError(f'El dominio "{domain_name}" ya existe')
        
        return domain_name
    
    @staticmethod
    def validate_email(email):
        email = email.lower().strip()
        
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise ValidationError('Email inválido')
        
        if Tenant.objects.filter(email=email).exists():
            raise ValidationError(f'El email "{email}" ya está en uso')
        
        return email
    
    @staticmethod
    def validate_username(username):
        username = username.strip()
        
        if User.objects.filter(username=username).exists():
            raise ValidationError(f'El username "{username}" ya existe')
        
        return username
    
    @staticmethod
    def create_complete_tenant(schema_name, tenant_name, email, phone, notes, domain_name, username, password):
        with transaction.atomic():
            tenant = Tenant.objects.create(
                schema_name=schema_name,
                name=tenant_name,
                email=email,
                phone=phone,
                notes=notes,
                status=Tenant.StatusChoices.ACTIVE,
                is_active=True
            )
            
            domain = Domain.objects.create(
                domain=domain_name,
                tenant=tenant,
                is_primary=True
            )
            
            TenantCreationService._migrate_tenant_schema(tenant)
            
            user = TenantCreationService._create_tenant_user(
                tenant, username, email, password
            )
            
            return tenant, domain, user
    
    @staticmethod
    def _migrate_tenant_schema(tenant):
        try:
            call_command('migrate_schemas', '--tenant', verbosity=0)
        except Exception:
            pass
    
    @staticmethod
    def _create_tenant_user(tenant, username, email, password):
        with schema_context(tenant.schema_name):
            return User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=False,
                is_superuser=False,
                tenant=tenant
            )
