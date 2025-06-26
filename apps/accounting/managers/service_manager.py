from django.db import models
from django.utils import timezone


class ServiceQuerySet(models.QuerySet):
    
    def active(self):
        return self.filter(is_active=True)
    
    def with_payments(self):
        return self.filter(payments__isnull=False).distinct()
    
    def by_category(self, category):
        return self.filter(category=category)
    
    def by_business_line(self, business_line):
        return self.filter(business_line=business_line)
    
    def expiring_soon(self, days=30):
        from ..services.payment_service import PaymentService
        
        services = []
        for service in self.active():
            active_until = PaymentService.get_service_active_until(service)
            if active_until:
                days_left = (active_until - timezone.now().date()).days
                if 0 <= days_left <= days:
                    services.append(service.pk)
        
        return self.filter(pk__in=services)
    
    def expired(self):
        from ..services.payment_service import PaymentService
        
        services = []
        for service in self.active():
            active_until = PaymentService.get_service_active_until(service)
            if active_until and active_until < timezone.now().date():
                services.append(service.pk)
        
        return self.filter(pk__in=services)
    
    def with_status(self, status):
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()
        
        base_filter = models.Q(is_active=True)
        
        if status == 'inactive':
            return self.filter(is_active=False)
        elif status == 'disabled':
            return self.filter(base_filter, admin_status='DISABLED')
        elif status == 'expired':
            return self.filter(base_filter, admin_status='ENABLED', end_date__lt=today)
        elif status == 'active':
            return self.filter(
                base_filter & 
                models.Q(admin_status='ENABLED') &
                (models.Q(end_date__isnull=True) | models.Q(end_date__gte=today + timedelta(days=30)))
            )
        elif status == 'renewal_due':
            return self.filter(
                base_filter,
                admin_status='ENABLED', 
                end_date__gte=today + timedelta(days=7),
                end_date__lt=today + timedelta(days=30)
            )
        elif status == 'expiring_soon':
            return self.filter(
                base_filter,
                admin_status='ENABLED',
                end_date__gte=today,
                end_date__lt=today + timedelta(days=7)
            )
        
        return self.none()


class ServiceManager(models.Manager):
    
    def get_queryset(self):
        return ServiceQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def with_payments(self):
        return self.get_queryset().with_payments()
    
    def by_category(self, category):
        return self.get_queryset().by_category(category)
    
    def by_business_line(self, business_line):
        return self.get_queryset().by_business_line(business_line)
    
    def expiring_soon(self, days=30):
        return self.get_queryset().expiring_soon(days)
    
    def expired(self):
        return self.get_queryset().expired()
    
    def with_status(self, status):
        return self.get_queryset().with_status(status)
