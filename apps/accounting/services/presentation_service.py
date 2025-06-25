from typing import Dict, Any, List
from decimal import Decimal
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.core.constants import SERVICE_CATEGORIES, CATEGORY_CONFIG, CATEGORY_DEFAULTS
from apps.accounting.services.revenue_analytics_service import RevenueAnalyticsService


class BusinessLinePresentationService:
    LEVEL_CONFIG = {
        1: {
            'icon': 'building',
            'color': 'blue',
            'bg_class': 'bg-blue-100 dark:bg-blue-900/20',
            'text_class': 'text-blue-600 dark:text-blue-400',
            'badge_class': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
        },
        2: {
            'icon': 'users',
            'color': 'green',
            'bg_class': 'bg-green-100 dark:bg-green-900/20',
            'text_class': 'text-green-600 dark:text-green-400',
            'badge_class': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
        },
        3: {
            'icon': 'user',
            'color': 'purple',
            'bg_class': 'bg-purple-100 dark:bg-purple-900/20',
            'text_class': 'text-purple-600 dark:text-purple-400',
            'badge_class': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
        }
    }
    
    def get_level_styling(self, business_line) -> Dict[str, str]:
        config = self.LEVEL_CONFIG.get(business_line.level, self.LEVEL_CONFIG[3])
        return config
    
    def get_status_badge(self, business_line) -> Dict[str, str]:
        if business_line.is_active:
            return {
                'text': 'Activa',
                'class': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
            }
        else:
            return {
                'text': 'Inactiva', 
                'class': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
            }
    
    def get_level_badge(self, business_line) -> Dict[str, str]:
        config = self.get_level_styling(business_line)
        return {
            'text': f'Nivel {business_line.level}',
            'class': config['badge_class']
        }
    
    def prepare_display_data(self, business_line) -> Dict[str, Any]:
        return {
            'styling': self.get_level_styling(business_line),
            'status_badge': self.get_status_badge(business_line),
            'level_badge': self.get_level_badge(business_line),
            'has_slug': bool(business_line.slug),
            'has_description': bool(business_line.description),
            'has_remanente': getattr(business_line, 'has_remanente', False)
        }

class CategoryNormalizationService:
    @staticmethod
    def normalize_category_code(category_code: str) -> str:
        return category_code.upper() if category_code else CATEGORY_DEFAULTS['DEFAULT_CATEGORY']

class CategoryPresentationService(CategoryNormalizationService):
    def get_category_styling(self, category_code: str) -> Dict[str, str]:
        normalized_code = self.normalize_category_code(category_code)
        return CATEGORY_CONFIG.get(normalized_code, CATEGORY_CONFIG[CATEGORY_DEFAULTS['DEFAULT_CATEGORY']])
    
    def get_category_badge(self, category_code: str) -> Dict[str, str]:
        config = self.get_category_styling(category_code)
        return {
            'text': config['name'],
            'class': f"bg-{config['color']}-100 text-{config['color']}-800 dark:bg-{config['color']}-900 dark:text-{config['color']}-200"
        }


class FinancialFormatService:
    @staticmethod
    def format_currency(amount, currency: str = '€') -> str:
        if amount is None:
            return f"{currency}0.00"
        try:
            if isinstance(amount, str):
                amount = amount.strip()
                if not amount:
                    return f"{currency}0.00"
                amount = float(amount)
            elif hasattr(amount, 'strip'):
                amount = amount.strip()
                if not amount:
                    return f"{currency}0.00"
                amount = float(amount)
            if not isinstance(amount, (int, float, Decimal)):
                amount = float(amount)
        except (ValueError, TypeError):
            return f"{currency}0.00"
        formatted = f"{amount:,.2f}".replace(',', ' ')
        return f"{currency}{formatted}"
    
    @staticmethod
    def format_percentage(value, decimals: int = 1) -> str:
        if value is None:
            return "0.0%"
        try:
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return "0.0%"
                value = float(value)
            elif hasattr(value, 'strip'):
                value = value.strip()
                if not value:
                    return "0.0%"
                value = float(value)
            if not isinstance(value, (int, float)):
                value = float(value)
        except (ValueError, TypeError):
            return "0.0%"
        return f"{value:.{decimals}f}%"
    
    @staticmethod
    def format_count(count: int, singular: str, plural: str = None) -> str:
        if plural is None:
            plural = f"{singular}s"
        if count == 1:
            return f"{count} {singular}"
        else:
            return f"{count} {plural}"
    
    @staticmethod
    def calculate_percentage(part: Decimal, total: Decimal) -> float:
        if total is None or total == 0:
            return 0.0
        if part is None:
            return 0.0
        return float(part / total * 100)


class UIPermissionService:
    @staticmethod
    def can_edit_business_line(user, business_line) -> bool:
        return user.role == 'ADMIN'
    
    @staticmethod
    def can_view_advanced_stats(user) -> bool:
        return user.role in ['ADMIN', 'MANAGER']


class PresentationService:
    def __init__(self):
        self.business_line = BusinessLinePresentationService()
        self.category = CategoryPresentationService()
        self.financial = FinancialFormatService()
        self.permissions = UIPermissionService()
        self.revenue_analytics = RevenueAnalyticsService()
    
    def prepare_business_line_presentation(self, business_line, user=None) -> Dict[str, Any]:
        data = {
            'display': self.business_line.prepare_display_data(business_line),
            'formatted_created': business_line.created.strftime('%d/%m/%Y') if business_line.created else '',
        }
        if user:
            data['user_actions'] = self.permissions.get_user_actions(user, business_line)
            data['can_edit'] = self.permissions.can_edit_business_line(user, business_line)
            data['can_view_advanced'] = self.permissions.can_view_advanced_stats(user)
        return data
    
    def prepare_service_presentation(self, service) -> Dict[str, Any]:
        revenue_breakdown = self.revenue_analytics.get_service_revenue_breakdown(service)
        
        return {
            'current_pricing': {
                'amount': self.financial.format_currency(revenue_breakdown['current_pricing']['amount']),
                'payment_method': revenue_breakdown['current_pricing']['payment_method'],
                'period_start': revenue_breakdown['current_pricing']['period_start'],
                'period_end': revenue_breakdown['current_pricing']['period_end'],
            },
            'revenue_summary': {
                'total_revenue': self.financial.format_currency(revenue_breakdown['revenue_summary']['total_revenue']),
                'payment_count': revenue_breakdown['revenue_summary']['payment_count'],
                'avg_payment': self.financial.format_currency(revenue_breakdown['revenue_summary']['avg_payment']),
            },
            'category_badge': self.category.get_category_badge(service.category),
            'has_remanentes': bool(getattr(service, 'remanentes', None)),
            'payments_history': revenue_breakdown['payments_history']
        }
    
    def prepare_category_revenue_summary(
        self, 
        business_line, 
        category: str, 
        period_type: str = RevenueAnalyticsService.PeriodType.ALL_TIME
    ) -> Dict[str, Any]:
        
        revenue_summary = self.revenue_analytics.get_business_line_revenue_summary(
            business_line, category, period_type
        )
        
        return {
            'period': revenue_summary['period'],
            'total_revenue': self.financial.format_currency(revenue_summary['total_revenue']),
            'payment_count': revenue_summary['payment_count'],
            'service_count': revenue_summary['service_count'],
            'avg_payment': self.financial.format_currency(revenue_summary['avg_payment']),
            'avg_revenue_per_service': self.financial.format_currency(revenue_summary['avg_revenue_per_service']),
        }
