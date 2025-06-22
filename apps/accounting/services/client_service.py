from decimal import Decimal
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from apps.accounting.models import Client, ClientService
from apps.business_lines.models import BusinessLine

User = get_user_model()


class ClientServiceOperations:
    def create_client_service(self, client, business_line, category, price, 
                             payment_method, start_date, renewal_date=None, 
                             remanentes=None):
        with transaction.atomic():
            self._validate_service_creation(
                client, business_line, category, remanentes
            )
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
            service.full_clean()
            service.save()
            return service

    def update_client_service(self, service, **update_fields):
        with transaction.atomic():
            for field, value in update_fields.items():
                if hasattr(service, field):
                    setattr(service, field, value)
            if 'category' in update_fields or 'remanentes' in update_fields:
                self._validate_service_update(service)
            service.full_clean()
            service.save()
            return service

    def create_client(self, full_name, dni, gender, email='', phone='', notes=''):
        with transaction.atomic():
            if Client.objects.filter(dni=dni, is_deleted=False).exists():
                raise ValidationError({
                    'dni': f'Ya existe un cliente con DNI {dni}'
                })
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
        return ClientService.objects.filter(
            business_line=business_line,
            category=category,
            is_active=True
        ).select_related('client', 'business_line').order_by('client__full_name')

    def get_client_services_summary(self, client):
        from django.db.models import Sum, Count
        services = client.services.filter(is_active=True)
        summary = services.aggregate(
            total_services=Count('id'),
            total_revenue=Sum('price'),
            white_services=Count('id', filter=Q(category='WHITE')),
            black_services=Count('id', filter=Q(category='BLACK'))
        )
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
        with transaction.atomic():
            service.is_active = False
            if reason:
                service.notes = f"{service.notes}\n\nDesactivado: {reason}".strip()
            service.save(update_fields=['is_active', 'notes', 'updated_at'])
            return service

    def reactivate_service(self, service):
        with transaction.atomic():
            service.is_active = True
            service.save(update_fields=['is_active', 'updated_at'])
            return service

    def _validate_service_creation(self, client, business_line, category, remanentes):
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
        if category == 'BLACK':
            self._validate_remanentes(business_line, remanentes)
        elif remanentes:
            raise ValidationError({
                'remanentes': 'Los remanentes solo pueden configurarse para la categoría BLACK.'
            })

    def _validate_service_update(self, service):
        if service.category == 'BLACK':
            self._validate_remanentes(service.business_line, service.remanentes)
        elif service.remanentes:
            raise ValidationError({
                'remanentes': 'Los remanentes solo pueden configurarse para la categoría BLACK.'
            })

    def _validate_remanentes(self, business_line, remanentes):
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
