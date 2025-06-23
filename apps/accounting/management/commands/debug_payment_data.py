from django.core.management.base import BaseCommand
from django.db.models import Sum
from apps.accounting.models import ClientService, ServicePayment
from apps.business_lines.models import BusinessLine


class Command(BaseCommand):
    help = 'Debug payment data inconsistencies'

    def handle(self, *args, **options):
        self.stdout.write("=== DEBUG PAYMENT DATA ===\n")
        
        # Check Dani-Rubi business line
        try:
            dani_rubi = BusinessLine.objects.get(name__icontains="Dani-Rubi")
            self.stdout.write(f"Business Line: {dani_rubi.name}")
            
            # Get revenue from ServicePayments
            total_revenue = ServicePayment.objects.filter(
                client_service__business_line=dani_rubi,
                client_service__category='WHITE',
                status=ServicePayment.StatusChoices.PAID
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            self.stdout.write(f"Total Revenue from ServicePayments: €{total_revenue}")
            
            # Get all ClientServices for this business line
            services = ClientService.objects.filter(
                business_line=dani_rubi,
                category='WHITE'
            )
            
            self.stdout.write(f"\nClientServices found: {services.count()}")
            
            for service in services:
                self.stdout.write(f"\n--- Service: {service} ---")
                self.stdout.write(f"Client: {service.client.full_name}")
                self.stdout.write(f"Current Amount: €{service.current_amount}")
                self.stdout.write(f"Total Paid: €{service.total_paid}")
                self.stdout.write(f"Payment Count: {service.payment_count}")
                self.stdout.write(f"Payment Method: {service.get_payment_method_display()}")
                
                # List all payments for this service
                payments = service.payments.all()
                self.stdout.write(f"All Payments ({payments.count()}):")
                for payment in payments:
                    self.stdout.write(f"  - {payment.amount}€ ({payment.status}) - {payment.period_start} to {payment.period_end}")
        
        except BusinessLine.DoesNotExist:
            self.stdout.write("Dani-Rubi business line not found")
            
            # List all business lines
            self.stdout.write("\nAvailable business lines:")
            for bl in BusinessLine.objects.all():
                self.stdout.write(f"  - {bl.name}")
