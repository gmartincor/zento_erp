from typing import Dict, Any, List
from decimal import Decimal

class FormatService:
    @staticmethod
    def format_badge(text, color_class):
        return {
            'text': text,
            'class': f"bg-{color_class}-100 text-{color_class}-800 dark:bg-{color_class}-900 dark:text-{color_class}-200"
        }
    
    @staticmethod
    def format_status_badge(is_active, active_text="Activo", inactive_text="Inactivo"):
        if is_active:
            return {
                'text': active_text,
                'class': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
            }
        else:
            return {
                'text': inactive_text, 
                'class': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
            }
    
    @staticmethod
    def format_currency(value, decimals=2, currency_symbol='€'):
        if value is None:
            return f"{currency_symbol}0.00"
        
        if isinstance(value, str):
            try:
                value = Decimal(value)
            except:
                return f"{currency_symbol}0.00"
        
        return f"{currency_symbol}{value:.{decimals}f}"
