from typing import Optional, Dict, Any
from datetime import date, timedelta
from django.utils import timezone


class DateCalculator:
    
    @staticmethod
    def get_today() -> date:
        return timezone.now().date()
    
    @staticmethod
    def days_between(start_date: date, end_date: date) -> int:
        return (end_date - start_date).days
    
    @staticmethod
    def is_date_in_past(target_date: Optional[date]) -> bool:
        if not target_date:
            return False
        return target_date < DateCalculator.get_today()
    
    @staticmethod
    def is_date_today(target_date: Optional[date]) -> bool:
        if not target_date:
            return False
        return target_date == DateCalculator.get_today()
    
    @staticmethod
    def is_date_in_future(target_date: Optional[date]) -> bool:
        if not target_date:
            return False
        return target_date > DateCalculator.get_today()
    
    @staticmethod
    def add_months_to_date(base_date: date, months: int) -> date:
        year = base_date.year
        month = base_date.month + months
        
        while month > 12:
            year += 1
            month -= 12
        
        while month < 1:
            year -= 1
            month += 12
        
        try:
            return base_date.replace(year=year, month=month)
        except ValueError:
            new_date = base_date.replace(year=year, month=month, day=1)
            last_day = DateCalculator._get_last_day_of_month(year, month)
            return new_date.replace(day=min(base_date.day, last_day))
    
    @staticmethod
    def _get_last_day_of_month(year: int, month: int) -> int:
        import calendar
        return calendar.monthrange(year, month)[1]
    
    @staticmethod
    def format_days_difference(days: int) -> str:
        if days < 0:
            abs_days = abs(days)
            if abs_days == 1:
                return "hace 1 día"
            return f"hace {abs_days} días"
        elif days == 0:
            return "hoy"
        elif days == 1:
            return "mañana"
        else:
            return f"en {days} días"
    
    @staticmethod
    def calculate_service_duration(start_date: date, end_date: Optional[date] = None) -> Dict[str, Any]:
        """Calcula la duración de un servicio"""
        if not end_date:
            end_date = DateCalculator.get_today()
        
        duration = DateCalculator.days_between(start_date, end_date)
        months = duration // 30
        
        return {
            'days': duration,
            'months': months,
            'years': duration // 365
        }
