"""
Client Service - Enhanced client and service operations.

This service handles all business logic related to clients and their services,
providing a clean interface for CRUD operations and business validations.
"""

from decimal import Decimal
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from apps.accounting.models import Client, ClientService
from apps.business_lines.models import BusinessLine

User = get_user_model()


class ClientServiceOperations:
    """
    Service class for client and client service operations.
    
    Centralizes business logic for:
    - Client management
    - Service creation and updates
    - Business rule validation
    - Complex queries and operations
    """
    
    def create_client_service(self, client, business_line, category, price, 
                             payment_method, start_date, renewal_date=None, 
                             remanentes=None):
        """
        Create a new client service with comprehensive validation.
        
        Args:
            client: Client instance
            business_line: BusinessLine instance
            category: Service category (WHITE/BLACK)
            price: Service price
            payment_method: Payment method
            start_date: Service start date
            renewal_date: Optional renewal date
            remanentes: Optional remanentes data for BLACK category
            
        Returns:
            Created ClientService instance
            
        Raises:
            ValidationError: If validation fails
        """
        with transaction.atomic():
            # Validate business rules
            self._validate_service_creation(
                client, business_line, category, remanentes
            )
            
            # Create service instance
            service = ClientService(
                client=client,
                business_line=business_line,
                category=category,
                price=price,
                payment_method=payment_method,
                start_date=start_date,
                renewal_date=renewal_date,
                remanentes=remanentes or {}
            )
            
            # Save with validation
            service.full_clean()
            service.save()
            
            return service
    
    def update_client_service(self, service, **update_fields):
        """
        Update an existing client service with validation.
        
        Args:
            service: ClientService instance to update
            **update_fields: Fields to update
            
        Returns:
            Updated ClientService instance
        """
        with transaction.atomic():
            # Apply updates
            for field, value in update_fields.items():
                if hasattr(service, field):
                    setattr(service, field, value)
            
            # Validate if category or remanentes changed
            if 'category' in update_fields or 'remanentes' in update_fields:
                self._validate_service_update(service)
            
            # Save with validation
            service.full_clean()
            service.save()
            
            return service
    
    def create_client(self, full_name, dni, gender, email='', phone='', notes=''):
        """
        Create a new client with validation.
        
        Args:
            full_name: Client's full name
            dni: Client's DNI/NIE
            gender: Client's gender
            email: Optional email
            phone: Optional phone
            notes: Optional notes
            
        Returns:
            Created Client instance
            
        Raises:
            ValidationError: If validation fails
        """
        with transaction.atomic():
            # Check for duplicate DNI
            if Client.objects.filter(dni=dni, is_deleted=False).exists():
                raise ValidationError({
                    'dni': f'Ya existe un cliente con DNI {dni}'
                })
            
            # Create client
            client = Client(
                full_name=full_name,
                dni=dni,
                gender=gender,
                email=email,
                phone=phone,
                notes=notes
            )
            
            client.full_clean()
            client.save()
            
            return client
    
    def get_services_by_category(self, business_line, category):
        """
        Get services filtered by business line and category.
        
        Args:
            business_line: BusinessLine instance
            category: Service category
            
        Returns:
            QuerySet of ClientServices
        """
        return ClientService.objects.filter(
            business_line=business_line,
            category=category,
            is_active=True
        ).select_related('client', 'business_line').order_by('client__full_name')
    
    def get_client_services_summary(self, client):
        """
        Get comprehensive summary of a client's services.
        
        Args:
            client: Client instance
            
        Returns:
            Dictionary with client service summary
        """
        from django.db.models import Sum, Count
        
        services = client.services.filter(is_active=True)
        
        summary = services.aggregate(
            total_services=Count('id'),
            total_revenue=Sum('price'),
            white_services=Count('id', filter=Q(category='WHITE')),
            black_services=Count('id', filter=Q(category='BLACK'))
        )
        
        # Calculate remanente totals for BLACK services
        black_services = services.filter(category='BLACK')
        total_remanentes = sum(
            service.get_remanente_total() for service in black_services
        )
        
        return {
            **summary,
            'total_remanentes': Decimal(str(total_remanentes)),
            'active_business_lines': services.values_list(
                'business_line__name', flat=True
            ).distinct()
        }
    
    def deactivate_service(self, service, reason=''):
        """
        Deactivate a client service.
        
        Args:
            service: ClientService instance
            reason: Optional deactivation reason
            
        Returns:
            Updated ClientService instance
        """
        with transaction.atomic():
            service.is_active = False
            if reason:
                service.notes = f"{service.notes}\n\nDesactivado: {reason}".strip()
            
            service.save(update_fields=['is_active', 'notes', 'updated_at'])
            
            return service
    
    def reactivate_service(self, service):
        """
        Reactivate a client service.
        
        Args:
            service: ClientService instance
            
        Returns:
            Updated ClientService instance
        """
        with transaction.atomic():
            service.is_active = True
            service.save(update_fields=['is_active', 'updated_at'])
            
            return service
    
    # Private validation methods
    
    def _validate_service_creation(self, client, business_line, category, remanentes):
        """Validate service creation business rules."""
        # Check for duplicate service
        existing = ClientService.objects.filter(
            client=client,
            business_line=business_line,
            category=category,
            is_active=True
        ).exists()
        
        if existing:
            raise ValidationError(
                f'El cliente {client.full_name} ya tiene un servicio {category} '
                f'activo en {business_line.name}'
            )
        
        # Validate remanentes for BLACK category
        if category == 'BLACK':
            self._validate_remanentes(business_line, remanentes)
        elif remanentes:
            raise ValidationError({
                'remanentes': 'Los remanentes solo pueden configurarse para la categoría BLACK.'
            })
    
    def _validate_service_update(self, service):
        """Validate service update business rules."""
        if service.category == 'BLACK':
            self._validate_remanentes(service.business_line, service.remanentes)
        elif service.remanentes:
            raise ValidationError({
                'remanentes': 'Los remanentes solo pueden configurarse para la categoría BLACK.'
            })
    
    def _validate_remanentes(self, business_line, remanentes):
        """Validate remanentes configuration for BLACK category."""
        if not business_line.has_remanente or not business_line.remanente_field:
            raise ValidationError({
                'business_line': f'La línea de negocio "{business_line.name}" '
                                'no tiene un tipo de remanente configurado.'
            })
        
        if remanentes and isinstance(remanentes, dict):
            valid_keys = {business_line.remanente_field}
            invalid_keys = set(remanentes.keys()) - valid_keys
            
            if invalid_keys:
                raise ValidationError({
                    'remanentes': f'El campo de remanentes contiene claves no válidas: '
                                 f'{", ".join(invalid_keys)}. Solo se permite la clave '
                                 f'"{business_line.remanente_field}" para esta línea de negocio.'
                })
