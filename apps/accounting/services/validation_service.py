from typing import Dict, List, Optional
from django.core.exceptions import ValidationError
from django.db.models import Q

from apps.business_lines.models import BusinessLine
from apps.accounting.models import Client, ClientService


class ValidationService:
    @staticmethod
    def validate_client_service_creation(
        client: Client,
        business_line: BusinessLine,
        category: str,
        remanentes: Optional[Dict] = None
    ) -> None:
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
        
        ValidationService._validate_category_rules(category, business_line, remanentes)
    
    @staticmethod
    def validate_remanentes_structure(
        business_line: BusinessLine,
        remanentes: Dict
    ) -> None:
        if not isinstance(remanentes, dict):
            raise ValidationError("Los remanentes deben ser un diccionario válido")
        
        if not business_line.has_remanente or not business_line.remanente_field:
            raise ValidationError(
                f"La línea de negocio '{business_line.name}' no soporta remanentes"
            )
        
        valid_keys = {business_line.remanente_field}
        invalid_keys = set(remanentes.keys()) - valid_keys
        
        if invalid_keys:
            raise ValidationError(
                f"Claves no válidas en remanentes: {', '.join(invalid_keys)}. "
                f"Solo se permite la clave '{business_line.remanente_field}'"
            )
        
        for key, value in remanentes.items():
            ValidationService._validate_remanente_value(key, value)
    
    @staticmethod
    def validate_business_line_remanente_mapping(business_line: BusinessLine) -> None:
        if not business_line.has_remanente:
            return
        
        business_line_name = business_line.name.lower()
        expected_remanente = None
        
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
        if 'category' in update_data:
            new_category = update_data['category']
            if new_category != service.category:
                ValidationService._validate_category_change(service, new_category)
        
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
        required_fields = ['full_name', 'dni', 'gender']
        missing_fields = [
            field for field in required_fields 
            if not client_data.get(field)
        ]
        
        if missing_fields:
            raise ValidationError(
                f"Campos requeridos faltantes: {', '.join(missing_fields)}"
            )
        
        dni = client_data.get('dni', '').strip()
        if dni and not ValidationService._is_valid_dni_format(dni):
            raise ValidationError("Formato de DNI/NIE no válido")
        
        email = client_data.get('email', '').strip()
        if email and not ValidationService._is_valid_email_format(email):
            raise ValidationError("Formato de email no válido")
    
    @staticmethod
    def _validate_category_rules(
        category: str,
        business_line: BusinessLine,
        remanentes: Optional[Dict]
    ) -> None:
        if category == ClientService.CategoryChoices.BLACK:
            if remanentes:
                ValidationService.validate_remanentes_structure(business_line, remanentes)
            ValidationService.validate_business_line_remanente_mapping(business_line)
        
        elif category == ClientService.CategoryChoices.WHITE:
            if remanentes:
                raise ValidationError(
                    "Los remanentes no están permitidos para la categoría WHITE"
                )
    
    @staticmethod
    def _validate_category_change(
        service: ClientService,
        new_category: str
    ) -> None:
        if service.category == ClientService.CategoryChoices.BLACK and new_category == ClientService.CategoryChoices.WHITE:
            if service.remanentes:
                raise ValidationError(
                    "No se puede cambiar a categoría WHITE: "
                    "el servicio tiene remanentes configurados"
                )
        
        elif service.category == ClientService.CategoryChoices.WHITE and new_category == ClientService.CategoryChoices.BLACK:
            ValidationService.validate_business_line_remanente_mapping(service.business_line)
    
    @staticmethod
    def _validate_remanente_value(key: str, value) -> None:
        try:
            float(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"El valor del remanente '{key}' debe ser numérico"
            )
    
    @staticmethod
    def _is_valid_dni_format(dni: str) -> bool:
        import re
        pattern = r'^[0-9XYZ][0-9]{7}[TRWAGMYFPDXBNJZSQVHLCKE]$'
        return bool(re.match(pattern, dni.upper()))
    
    @staticmethod
    def _is_valid_email_format(email: str) -> bool:
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
