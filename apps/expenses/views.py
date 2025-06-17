from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Sum

from apps.expenses.models import Expense, ExpenseCategory


class ExpenseCategoryView(LoginRequiredMixin, TemplateView):
    """Vista principal que muestra categorías de gastos con totales."""
    template_name = 'expenses/categories.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calcular totales por tipo de categoría
        category_totals = {}
        total_general = 0
        
        for category_type, display_name in ExpenseCategory.CategoryTypeChoices.choices:
            total = Expense.objects.filter(
                category__category_type=category_type
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            category_totals[category_type] = {
                'name': display_name,
                'total': total,
                'count': Expense.objects.filter(category__category_type=category_type).count()
            }
            total_general += total
        
        context['category_totals'] = category_totals
        context['total_general'] = total_general
        
        return context


class ExpenseListView(LoginRequiredMixin, ListView):
    """Lista de gastos filtrada por categoría."""
    model = Expense
    template_name = 'expenses/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 25
    
    def get_queryset(self):
        category_type = self.kwargs['category_type']
        return Expense.objects.filter(
            category__category_type=category_type
        ).select_related('category').order_by('-date', '-created')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_type = self.kwargs['category_type']
        
        # Información de la categoría actual
        context['category_type'] = category_type
        context['category_display'] = dict(ExpenseCategory.CategoryTypeChoices.choices)[category_type]
        
        # Total de la categoría actual
        context['category_total'] = self.get_queryset().aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        return context


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    """Crear un nuevo gasto en una categoría específica."""
    model = Expense
    fields = ['description', 'amount', 'date', 'category', 'invoice_number']
    template_name = 'expenses/expense_form.html'
    
    def get_success_url(self):
        category_type = self.kwargs['category_type']
        return reverse_lazy('expenses:by-category', kwargs={'category_type': category_type})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_type = self.kwargs['category_type']
        
        context['category_type'] = category_type
        context['category_display'] = dict(ExpenseCategory.CategoryTypeChoices.choices)[category_type]
        context['form_title'] = f'Nuevo Gasto {context["category_display"]}'
        
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        category_type = self.kwargs['category_type']
        
        # Filtrar categorías por tipo
        form.fields['category'].queryset = ExpenseCategory.objects.filter(
            category_type=category_type,
            is_active=True
        )
        
        return form


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    """Actualizar un gasto existente."""
    model = Expense
    fields = ['description', 'amount', 'date', 'category', 'invoice_number']
    template_name = 'expenses/expense_form.html'
    
    def get_success_url(self):
        category_type = self.kwargs['category_type']
        return reverse_lazy('expenses:by-category', kwargs={'category_type': category_type})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_type = self.kwargs['category_type']
        
        context['category_type'] = category_type
        context['category_display'] = dict(ExpenseCategory.CategoryTypeChoices.choices)[category_type]
        context['form_title'] = f'Editar Gasto {context["category_display"]}'
        
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        category_type = self.kwargs['category_type']
        
        # Filtrar categorías por tipo
        form.fields['category'].queryset = ExpenseCategory.objects.filter(
            category_type=category_type,
            is_active=True
        )
        
        return form


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar un gasto."""
    model = Expense
    template_name = 'expenses/expense_confirm_delete.html'
    
    def get_success_url(self):
        category_type = self.kwargs['category_type']
        return reverse_lazy('expenses:by-category', kwargs={'category_type': category_type})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_type = self.kwargs['category_type']
        
        context['category_type'] = category_type
        context['category_display'] = dict(ExpenseCategory.CategoryTypeChoices.choices)[category_type]
        
        return context
