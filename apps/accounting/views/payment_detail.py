from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from ..models import ServicePayment


@login_required
@require_http_methods(["GET"])
def payment_detail_view(request, payment_id):
    payment = get_object_or_404(ServicePayment, id=payment_id)
    
    context = {
        'payment': payment,
        'client_service': payment.client_service,
        'client': payment.client_service.client,
    }
    
    return render(request, 'accounting/payment_detail.html', context)
