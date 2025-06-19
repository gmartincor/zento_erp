"""
Validation Service - Centralized business validation logic.

This service handles all business rule validation for the accounting module,
ensuring data integrity and business logic compliance.
"""

from typing import Dict, List, Optional
from django.core.exceptions import ValidationError
from django.db.models import Q

from apps.business_lines.models import BusinessLine
from apps.accounting.models import Client, ClientService


class ValidationService:
    """
    Service class for business validation logic.
    
    Centralizes validation rules and business logic validation
    to ensure consistency across the application.
    """
    
    @staticmethod
    def validate_client_service_creation(
        client: Client,
        business_line: BusinessLine,
        category: str,
        remanentes: Optional[Dict] = None
    ) -> None:
        """
        Validate business rules for creating a new client service.
        
        Args:
            client: Client instance
            business_line: BusinessLine instance
            category: Service category (WHITE/BLACK)
            remanentes: Optional remanentes data
            
        Raises:
            ValidationError: If validation fails
        """
        # Check for existing active service
        existing = ClientService.objects.filter(
            client=client,
            business_line=business_line,
            category=category,
            is_active=True
        ).exists()
        
        if existing:
            raise ValidationError(
                f"El cliente {client.full_name} ya tiene un servicio activo "
                f"de categoría {category} en la línea de negocio {business_line.name}"
            )
        
        # Validate category-specific rules
        ValidationService._validate_category_rules(category, business_line, remanentes)
    
    @staticmethod
    def validate_remanentes_structure(
        business_line: BusinessLine,
        remanentes: Dict
    ) -> None:
        """
        Validate remanentes structure for a business line.
        
        Args:
            business_line: BusinessLine instance
            remanentes: Remanentes dictionary to validate
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(remanentes, dict):
            raise ValidationError("Los remanentes deben ser un diccionario válido")
        
        # Check if business line supports remanentes
        if not business_line.has_remanente or not business_line.remanente_field:
            raise ValidationError(
                f"La línea de negocio '{business_line.name}' no soporta remanentes"
            )
        
        # Validate keys
        valid_keys = {business_line.remanente_field}
        invalid_keys = set(remanentes.keys()) - valid_keys
        
        if invalid_keys:
            raise ValidationError(
                f"Claves no válidas en remanentes: {', '.join(invalid_keys)}. "
                f"Solo se permite la clave '{business_line.remanente_field}'"
            )
        
        # Validate values
        for key, value in remanentes.items():
            ValidationService._validate_remanente_value(key, value)
    
    @staticmethod
    def validate_business_line_remanente_mapping(business_line: BusinessLine) -> None:
        """
        Validate that business line has correct remanente field mapping.
        
        Args:
            business_line: BusinessLine to validate
            
        Raises:
            ValidationError: If mapping is incorrect
        """
        if not business_line.has_remanente:
            return
        
        business_line_name = business_line.name.lower()
        expected_remanente = None
        
        # Define expected mappings
        if "pepe-normal" in business_line_name:
            expected_remanente = BusinessLine.RemanenteChoices.REMANENTE_PEPE
        elif "pepe-videocall" in business_line_name:
            expected_remanente = BusinessLine.RemanenteChoices.REMANENTE_PEPE_VIDEO
        elif "dani-rubi" in business_line_name:
            expected_remanente = BusinessLine.RemanenteChoices.REMANENTE_DANI
        elif "dani" in business_line_name and "rubi" not in business_line_name:
            expected_remanente = BusinessLine.RemanenteChoices.REMANENTE_AVEN
        
        if expected_remanente and business_line.remanente_field != expected_remanente:
            raise ValidationError(
                f"La línea de negocio '{business_line.name}' debe usar el tipo "
                f"de remanente '{expected_remanente}'"
            )
    
    @staticmethod
    def validate_service_update(
        service: ClientService,
        update_data: Dict
    ) -> None:
        """
        Validate service update data.
        
        Args:
            service: ClientService being updated
            update_data: Dictionary of fields being updated
            
        Raises:
            ValidationError: If update is invalid
        """
        # If category is being changed, validate the change
        if 'category' in update_data:
            new_category = update_data['category']
            if new_category != service.category:
                ValidationService._validate_category_change(service, new_category)
        
        # If remanentes are being updated, validate them
        if 'remanentes' in update_data:
            new_remanentes = update_data['remanentes']
            category = update_data.get('category', service.category)
            
            if category == ClientService.CategoryChoices.BLACK:
                ValidationService.validate_remanentes_structure(
                    service.business_line,
                    new_remanentes
                )
            elif new_remanentes:
                raise ValidationError(
                    "Los remanentes solo pueden configurarse para la categoría BLACK"
                )
    
    @staticmethod
    def validate_client_data(client_data: Dict) -> None:
        """
        Validate client data before creation or update.
        
        Args:
            client_data: Dictionary with client data
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        required_fields = ['full_name', 'dni', 'gender']
        missing_fields = [
            field for field in required_fields 
            if not client_data.get(field)
        ]
        
        if missing_fields:
            raise ValidationError(
                f"Campos requeridos faltantes: {', '.join(missing_fields)}"
            )
        
        # Validate DNI format (basic validation)
        dni = client_data.get('dni', '').strip()
        if dni and not ValidationService._is_valid_dni_format(dni):
            raise ValidationError("Formato de DNI/NIE no válido")
        
        # Validate email if provided
        email = client_data.get('email', '').strip()
        if email and not ValidationService._is_valid_email_format(email):
            raise ValidationError("Formato de email no válido")
    
    @staticmethod
    def _validate_category_rules(
        category: str,
        business_line: BusinessLine,
        remanentes: Optional[Dict]
    ) -> None:
        """Validate category-specific business rules."""
        if category == ClientService.CategoryChoices.BLACK:
            # BLACK category specific validations
            if remanentes:
                ValidationService.validate_remanentes_structure(business_line, remanentes)
            
            # Validate business line supports BLACK category
            ValidationService.validate_business_line_remanente_mapping(business_line)
        
        elif category == ClientService.CategoryChoices.WHITE:
            # WHITE category should not have remanentes
            if remanentes:
                raise ValidationError(
                    "Los remanentes no están permitidos para la categoría WHITE"
                )
    
    @staticmethod
    def _validate_category_change(
        service: ClientService,
        new_category: str
    ) -> None:
        """Validate category change for existing service."""
        if service.category == ClientService.CategoryChoices.BLACK and new_category == ClientService.CategoryChoices.WHITE:
            # Changing from BLACK to WHITE - warn about remanentes loss
            if service.remanentes:
                raise ValidationError(
                    "No se puede cambiar a categoría WHITE: "
                    "el servicio tiene remanentes configurados"
                )
        
        elif service.category == ClientService.CategoryChoices.WHITE and new_category == ClientService.CategoryChoices.BLACK:
            # Changing from WHITE to BLACK - validate business line supports it
            ValidationService.validate_business_line_remanente_mapping(service.business_line)
    
    @staticmethod
    def _validate_remanente_value(key: str, value) -> None:
        """Validate individual remanente value."""
        try:
            # Try to convert to float to validate numeric format
            float(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"El valor del remanente '{key}' debe ser numérico"
            )
    
    @staticmethod
    def _is_valid_dni_format(dni: str) -> bool:
        """Basic DNI format validation."""
        import re
        # Basic pattern for Spanish DNI/NIE
        pattern = r'^[0-9XYZ][0-9]{7}[TRWAGMYFPDXBNJZSQVHLCKE]$'
        return bool(re.match(pattern, dni.upper()))
    
    @staticmethod
    def _is_valid_email_format(email: str) -> bool:
        """Basic email format validation."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
