from typing import Dict, Any, Optional
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from apps.accounting.models import ClientService, ServicePayment
from apps.accounting.forms import RenewalForm, PaymentCreateForm, PaymentUpdateForm, PaymentFilterForm
from apps.accounting.services.payment_service import PaymentService
from apps.accounting.services.business_line_service import BusinessLineService
from apps.accounting.services.service_flow_manager import ServiceContextBuilder
from apps.accounting.services.service_workflow_manager import ServiceWorkflowManager


@login_required
def payment_list(request, business_line_path: str = None):
    business_line_service = BusinessLineService()
    
    if business_line_path:
        business_line = business_line_service.get_business_line_by_path(business_line_path)
        if not business_line:
            messages.error(request, 'Línea de negocio no encontrada.')
            return redirect('accounting:index')
        
        accessible_lines = business_line_service.get_accessible_lines(request.user)
        if business_line not in accessible_lines:
            messages.error(request, 'No tienes permisos para acceder a esta línea de negocio.')
            return redirect('accounting:index')
        
        services = ClientService.objects.filter(business_line=business_line)
        page_title = f'Pagos - {business_line.name}'
    else:
        accessible_lines = business_line_service.get_accessible_lines(request.user)
        services = ClientService.objects.filter(business_line__in=accessible_lines)
        business_line = None
        page_title = 'Todos los Pagos'
    
    payments = ServicePayment.objects.filter(
        client_service__in=services
    ).select_related(
        'client_service__client',
        'client_service__business_line'
    ).order_by('-payment_date')
    
    filter_form = PaymentFilterForm(request.GET)
    
    if filter_form.is_valid():
        cleaned_data = filter_form.cleaned_data
        
        if cleaned_data.get('status'):
            payments = payments.filter(status=cleaned_data['status'])
        
        if cleaned_data.get('payment_method'):
            payments = payments.filter(payment_method=cleaned_data['payment_method'])
        
        if cleaned_data.get('date_from'):
            payments = payments.filter(payment_date__gte=cleaned_data['date_from'])
        
        if cleaned_data.get('date_to'):
            payments = payments.filter(payment_date__lte=cleaned_data['date_to'])
        
        if cleaned_data.get('amount_from'):
            payments = payments.filter(amount__gte=cleaned_data['amount_from'])
        
        if cleaned_data.get('amount_to'):
            payments = payments.filter(amount__lte=cleaned_data['amount_to'])
    
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'business_line': business_line,
        'page_title': page_title,
        'total_payments': payments.count(),
    }
    
    return render(request, 'accounting/payments/payment_list.html', context)


@login_required
def payment_detail(request, payment_id: int):
    payment = get_object_or_404(
        ServicePayment.objects.select_related(
            'client_service__client',
            'client_service__business_line'
        ),
        id=payment_id
    )
    
    business_line_service = BusinessLineService()
    accessible_lines = business_line_service.get_accessible_lines(request.user)
    
    if payment.client_service.business_line not in accessible_lines:
        messages.error(request, 'No tienes permisos para ver este pago.')
        return redirect('accounting:payments')
    
    context = {
        'payment': payment,
        'client_service': payment.client_service,
    }
    
    return render(request, 'accounting/payments/payment_detail.html', context)


@login_required
def service_renewal(request, service_id: int):
    client_service = get_object_or_404(ClientService, id=service_id)
    
    business_line_service = BusinessLineService()
    accessible_lines = business_line_service.get_accessible_lines(request.user)
    
    if client_service.business_line not in accessible_lines:
        messages.error(request, 'No tienes permisos para renovar este servicio.')
        return redirect('accounting:index')
    
    if request.method == 'POST':
        form = RenewalForm(request.POST, client_service=client_service)
        if form.is_valid():
            try:
                payment = form.save()
                messages.success(
                    request,
                    f'Renovación procesada exitosamente. '
                    f'Servicio activo hasta {payment.period_end.strftime("%d/%m/%Y")}.'
                )
                return redirect('accounting:payment-detail', payment_id=payment.id)
            except Exception as e:
                messages.error(request, f'Error al procesar la renovación: {str(e)}')
    else:
        form = RenewalForm(client_service=client_service)
    
    context = {
        'form': form,
        'client_service': client_service,
        'next_renewal_date': PaymentService.get_next_renewal_date(client_service),
    }
    
    return render(request, 'accounting/payments/service_renewal.html', context)


@login_required
def payment_create(request, service_id: int):
    client_service = get_object_or_404(ClientService, id=service_id)
    
    business_line_service = BusinessLineService()
    accessible_lines = business_line_service.get_accessible_lines(request.user)
    
    if client_service.business_line not in accessible_lines:
        messages.error(request, 'No tienes permisos para crear pagos para este servicio.')
        return redirect('accounting:index')
    
    if request.method == 'POST':
        form = PaymentCreateForm(request.POST, client_service=client_service)
        if form.is_valid():
            try:
                payment, redirect_url = ServiceWorkflowManager.handle_payment_creation_flow(
                    request, service_id, form.cleaned_data
                )
                return redirect(redirect_url)
            except Exception as e:
                messages.error(request, f'Error al crear el pago: {str(e)}')
    else:
        form = PaymentCreateForm(client_service=client_service)
    
    context_builder = ServiceContextBuilder(client_service)
    context = context_builder.build_base_context()
    context.update({
        'form': form,
        'page_title': f'Nuevo Pago - {client_service.client.full_name}'
    })
    
    return render(request, 'accounting/payments/payment_create.html', context)


@login_required
def payment_update(request, payment_id: int):
    payment = get_object_or_404(ServicePayment, id=payment_id)
    
    business_line_service = BusinessLineService()
    accessible_lines = business_line_service.get_accessible_lines(request.user)
    
    if payment.client_service.business_line not in accessible_lines:
        messages.error(request, 'No tienes permisos para editar este pago.')
        return redirect('accounting:payments')
    
    if payment.status == ServicePayment.StatusChoices.PAID:
        messages.warning(
            request,
            'Los pagos completados tienen campos de solo lectura para mantener la integridad de los datos.'
        )
    
    if request.method == 'POST':
        form = PaymentUpdateForm(request.POST, instance=payment, client_service=payment.client_service)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Pago actualizado exitosamente.')
                return redirect('accounting:payment-detail', payment_id=payment.id)
            except Exception as e:
                messages.error(request, f'Error al actualizar el pago: {str(e)}')
    else:
        form = PaymentUpdateForm(instance=payment, client_service=payment.client_service)
    
    context = {
        'form': form,
        'payment': payment,
        'client_service': payment.client_service,
    }
    
    return render(request, 'accounting/payments/payment_update.html', context)


@login_required
@require_http_methods(["POST"])
def payment_mark_paid(request, payment_id: int):
    payment = get_object_or_404(ServicePayment, id=payment_id)
    
    business_line_service = BusinessLineService()
    accessible_lines = business_line_service.get_accessible_lines(request.user)
    
    if payment.client_service.business_line not in accessible_lines:
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    if payment.status != ServicePayment.StatusChoices.PENDING:
        return JsonResponse({'error': 'Solo se pueden marcar como pagados los pagos pendientes'}, status=400)
    
    try:
        payment.mark_as_paid()
        return JsonResponse({
            'success': True,
            'message': 'Pago marcado como pagado',
            'new_status': payment.get_status_display()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def payment_cancel(request, payment_id: int):
    payment = get_object_or_404(ServicePayment, id=payment_id)
    
    business_line_service = BusinessLineService()
    accessible_lines = business_line_service.get_accessible_lines(request.user)
    
    if payment.client_service.business_line not in accessible_lines:
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    if payment.status not in [ServicePayment.StatusChoices.PENDING, ServicePayment.StatusChoices.OVERDUE]:
        return JsonResponse({'error': 'Solo se pueden cancelar pagos pendientes o vencidos'}, status=400)
    
    try:
        reason = request.POST.get('reason', 'Cancelado por usuario')
        payment.cancel(reason)
        return JsonResponse({
            'success': True,
            'message': 'Pago cancelado',
            'new_status': payment.get_status_display()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def service_payment_history(request, service_id: int):
    client_service = get_object_or_404(ClientService, id=service_id)
    
    business_line_service = BusinessLineService()
    accessible_lines = business_line_service.get_accessible_lines(request.user)
    
    if client_service.business_line not in accessible_lines:
        messages.error(request, 'No tienes permisos para ver el historial de este servicio.')
        return redirect('accounting:index')
    
    payments = PaymentService.get_payment_history(client_service)
    
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context_builder = ServiceContextBuilder(client_service)
    context = context_builder.build_payment_context()
    context.update({
        'page_obj': page_obj,
    })
    
    return render(request, 'accounting/payments/service_history.html', context)


@login_required
def expiring_services(request):
    business_line_service = BusinessLineService()
    accessible_lines = business_line_service.get_accessible_lines(request.user)
    
    days_ahead = int(request.GET.get('days', 30))
    expiring_data = PaymentService.get_expiring_services(days_ahead)
    
    # Filtrar por líneas accesibles
    filtered_data = [
        (service, payment) for service, payment in expiring_data
        if service.business_line in accessible_lines
    ]
    
    context = {
        'expiring_services': filtered_data,
        'days_ahead': days_ahead,
        'total_expiring': len(filtered_data),
    }
    
    return render(request, 'accounting/payments/expiring_services.html', context)
