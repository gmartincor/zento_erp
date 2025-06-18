"""
Utilities for the accounting module.
Business logic and helper functions for revenue management.
"""

from django.db.models import Q, Sum, Count
from django.core.exceptions import ValidationError
from apps.business_lines.models import BusinessLine
from apps.accounting.models import ClientService


class BusinessLineNavigator:
    """
    Utility class for navigating business line hierarchies and resolving paths.
    
    Provides static methods for common business line operations without
    requiring view context.
    """
    
    @staticmethod
    def get_business_line_by_path(line_path):
        """
        Get a business line by its hierarchical path.
        
        Args:
            line_path (str): Path like 'jaen/pepe/pepe-normal'
            
        Returns:
            BusinessLine: The resolved business line object
            
        Raises:
            BusinessLine.DoesNotExist: If path doesn't resolve to valid business line
        """
        if not line_path:
            raise BusinessLine.DoesNotExist("Empty path provided")
        
        path_parts = line_path.strip('/').split('/')
        
        if len(path_parts) == 1:
            return BusinessLine.objects.get(slug=path_parts[0], level=1)
        
        # Navigate through hierarchy
        current_line = None
        for i, slug in enumerate(path_parts):
            if i == 0:
                current_line = BusinessLine.objects.get(slug=slug, level=1)
            else:
                current_line = BusinessLine.objects.get(
                    slug=slug,
                    parent=current_line,
                    level=i + 1
                )
        
        return current_line
    
    @staticmethod
    def build_line_path(business_line):
        """
        Build hierarchical path string for a business line.
        
        Args:
            business_line (BusinessLine): Business line object
            
        Returns:
            str: Path string like 'jaen/pepe/pepe-normal'
        """
        if not business_line:
            return ''
        
        path_parts = []
        current = business_line
        
        while current:
            path_parts.insert(0, current.slug)
            current = current.parent
        
        return '/'.join(path_parts)
    
    @staticmethod
    def get_children_for_display(business_line, user_permissions=None):
        """
        Get child business lines suitable for navigation display.
        
        Args:
            business_line (BusinessLine): Parent business line
            user_permissions (QuerySet, optional): User's allowed business lines
            
        Returns:
            QuerySet: Child business lines with service counts
        """
        children = business_line.children.filter(is_active=True)
        
        if user_permissions is not None:
            children = children.filter(id__in=user_permissions.values_list('id', flat=True))
        
        # Annotate with service counts for display
        children = children.annotate(
            white_service_count=Count(
                'client_services',
                filter=Q(client_services__category='WHITE', client_services__is_active=True)
            ),
            black_service_count=Count(
                'client_services',
                filter=Q(client_services__category='BLACK', client_services__is_active=True)
            )
        ).order_by('name')
        
        return children
    
    @staticmethod
    def get_root_lines_for_user(user):
        """
        Get root-level business lines accessible to a user.
        
        Args:
            user: User object with role and business_lines relationship
            
        Returns:
            QuerySet: Root business lines with access counts
        """
        if user.role == 'ADMIN':
            root_lines = BusinessLine.objects.filter(level=1, is_active=True)
        elif user.role == 'GLOW_VIEWER':
            # Get root lines that contain user's assigned lines
            assigned_lines = user.business_lines.all()
            root_ids = set()
            
            for line in assigned_lines:
                # Find root ancestor
                current = line
                while current.parent:
                    current = current.parent
                root_ids.add(current.id)
            
            root_lines = BusinessLine.objects.filter(
                id__in=root_ids,
                level=1,
                is_active=True
            )
        else:
            root_lines = BusinessLine.objects.none()
        
        # Annotate with total service counts
        return root_lines.annotate(
            total_services=Count(
                'client_services',
                filter=Q(client_services__is_active=True)
            ),
            total_revenue=Sum(
                'client_services__price',
                filter=Q(client_services__is_active=True)
            )
        ).order_by('name')


class ServiceStatisticsCalculator:
    """
    Utility class for calculating service and revenue statistics.
    
    Provides methods for various statistical calculations across
    business lines and service categories.
    """
    
    @staticmethod
    def calculate_business_line_stats(business_line, include_children=True):
        """
        Calculate comprehensive statistics for a business line.
        
        Args:
            business_line (BusinessLine): Business line to analyze
            include_children (bool): Whether to include child line statistics
            
        Returns:
            dict: Statistics dictionary with revenue, counts, and breakdowns
        """
        from django.db.models import Q
        
        # Base filter for this business line
        base_filter = Q(business_line=business_line, is_active=True)
        
        if include_children:
            # Include all descendant business lines
            descendant_ids = [business_line.id]
            ServiceStatisticsCalculator._collect_descendant_ids(business_line, descendant_ids)
            base_filter = Q(business_line_id__in=descendant_ids, is_active=True)
        
        services = ClientService.objects.filter(base_filter)
        
        # Basic aggregations
        stats = services.aggregate(
            total_revenue=Sum('price'),
            total_services=Count('id'),
            white_services=Count('id', filter=Q(category='WHITE')),
            black_services=Count('id', filter=Q(category='BLACK')),
            white_revenue=Sum('price', filter=Q(category='WHITE')),
            black_revenue=Sum('price', filter=Q(category='BLACK'))
        )
        
        # Calculate remanente totals for BLACK services
        black_services = services.filter(category='BLACK')
        total_remanentes = sum(service.get_remanente_total() for service in black_services)
        
        # Calculate averages
        total_count = stats['total_services'] or 0
        avg_revenue_per_service = (stats['total_revenue'] or 0) / max(total_count, 1)
        
        return {
            'total_revenue': stats['total_revenue'] or 0,
            'total_services': total_count,
            'white_services': stats['white_services'] or 0,
            'black_services': stats['black_services'] or 0,
            'white_revenue': stats['white_revenue'] or 0,
            'black_revenue': stats['black_revenue'] or 0,
            'total_remanentes': total_remanentes,
            'avg_revenue_per_service': avg_revenue_per_service,
        }
    
    @staticmethod
    def _collect_descendant_ids(business_line, id_list):
        """Helper method to recursively collect descendant IDs."""
        for child in business_line.children.filter(is_active=True):
            id_list.append(child.id)
            ServiceStatisticsCalculator._collect_descendant_ids(child, id_list)
    
    @staticmethod
    def get_revenue_summary_by_period(business_lines, year=None, month=None):
        """
        Get revenue summary for business lines filtered by time period.
        
        Args:
            business_lines (QuerySet): Business lines to analyze
            year (int, optional): Filter by year
            month (int, optional): Filter by month
            
        Returns:
            dict: Summary with revenue totals and breakdowns
        """
        filters = Q(business_line__in=business_lines, is_active=True)
        
        if year:
            filters &= Q(start_date__year=year)
        if month:
            filters &= Q(start_date__month=month)
        
        services = ClientService.objects.filter(filters)
        
        summary = services.aggregate(
            total_revenue=Sum('price'),
            total_services=Count('id'),
            unique_clients=Count('client', distinct=True)
        )
        
        # Group by business line for breakdown
        line_breakdown = {}
        for line in business_lines:
            line_services = services.filter(business_line=line)
            line_stats = line_services.aggregate(
                revenue=Sum('price'),
                count=Count('id')
            )
            
            line_breakdown[line.id] = {
                'name': line.name,
                'revenue': line_stats['revenue'] or 0,
                'count': line_stats['count'] or 0,
                'slug': line.slug
            }
        
        return {
            'summary': summary,
            'breakdown': line_breakdown,
            'period': {
                'year': year,
                'month': month
            }
        }


class RemanentesValidator:
    """
    Utility class for validating remanente configurations and calculations.
    
    Provides validation methods for remanente business rules and data integrity.
    """
    
    @staticmethod
    def validate_remanente_for_business_line(business_line, remanentes_data):
        """
        Validate remanente data for a specific business line.
        
        Args:
            business_line (BusinessLine): Business line object
            remanentes_data (dict): Remanente data to validate
            
        Returns:
            dict: Validated and cleaned remanente data
            
        Raises:
            ValidationError: If validation fails
        """
        if not business_line.has_remanente:
            if remanentes_data:
                raise ValidationError(
                    f"La línea de negocio '{business_line.name}' no permite remanentes."
                )
            return {}
        
        if not business_line.remanente_field:
            raise ValidationError(
                f"La línea de negocio '{business_line.name}' no tiene configurado un tipo de remanente."
            )
        
        # Validate that only the correct remanente field is used
        valid_key = business_line.remanente_field
        cleaned_data = {}
        
        for key, value in remanentes_data.items():
            if key == valid_key:
                try:
                    # Validate numeric value
                    cleaned_value = float(value)
                    cleaned_data[key] = cleaned_value
                except (ValueError, TypeError):
                    raise ValidationError(
                        f"El valor del remanente '{key}' debe ser numérico."
                    )
            else:
                raise ValidationError(
                    f"Campo de remanente '{key}' no válido para la línea '{business_line.name}'. "
                    f"Solo se permite '{valid_key}'."
                )
        
        return cleaned_data
    
    @staticmethod
    def get_expected_remanente_field(business_line_name):
        """
        Get the expected remanente field based on business line name patterns.
        
        Args:
            business_line_name (str): Name of the business line
            
        Returns:
            str or None: Expected remanente field name
        """
        name_lower = business_line_name.lower()
        
        if "pepe-normal" in name_lower:
            return BusinessLine.RemanenteChoices.REMANENTE_PEPE
        elif "pepe-videocall" in name_lower:
            return BusinessLine.RemanenteChoices.REMANENTE_PEPE_VIDEO
        elif "dani-rubi" in name_lower:
            return BusinessLine.RemanenteChoices.REMANENTE_DANI
        elif "dani" in name_lower and "rubi" not in name_lower:
            return BusinessLine.RemanenteChoices.REMANENTE_AVEN
        
        return None
