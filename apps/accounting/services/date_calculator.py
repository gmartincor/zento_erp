from datetime import date, timedelta
from typing import Optional


class DateCalculator:
    
    @classmethod
    def add_months_to_date(cls, start_date: date, months: int) -> date:
        year = start_date.year
        month = start_date.month + months
        day = start_date.day
        
        while month > 12:
            month -= 12
            year += 1
        
        try:
            return date(year, month, day)
        except ValueError:
            return date(year, month + 1, 1) - timedelta(days=1)
    
    @classmethod
    def calculate_period_end(cls, start_date: date, duration_months: int) -> date:
        end_date = cls.add_months_to_date(start_date, duration_months)
        return end_date - timedelta(days=1)
    
    @classmethod
    def calculate_days_until(cls, target_date: Optional[date]) -> Optional[int]:
        if not target_date:
            return None
        from django.utils import timezone
        today = timezone.now().date()
        return (target_date - today).days
    
    @classmethod
    def calculate_days_since(cls, reference_date: Optional[date]) -> Optional[int]:
        if not reference_date:
            return None
        from django.utils import timezone
        today = timezone.now().date()
        return (today - reference_date).days
