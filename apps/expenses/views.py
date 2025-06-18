from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import Http404

from apps.expenses.models import Expense, ExpenseCategory
from apps.expenses.forms import ExpenseForm, ExpenseCategoryForm
from apps.core.mixins import TemporalFilterMixin, CategoryContextMixin
from apps.core.constants import SUCCESS_MESSAGES, ERROR_MESSAGES


class ExpenseCategoryView(LoginRequiredMixin, TemporalFilterMixin, TemplateView):
    """Vista principal que muestra categorías de gastos con totales."""
    template_name = 'expenses/categories.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener filtros temporales usando el mixin
        filters = self.get_temporal_filters()
        expense_filter = filters['expense_filter']
        year = filters['year']
        month = filters['month']
        
        # Calcular totales por tipo de categoría
        category_totals = {}
        total_general = 0
        
        for category_type, display_name in ExpenseCategory.CategoryTypeChoices.choices:
            filtered_expenses = Expense.objects.filter(
                category__category_type=category_type,
                **expense_filter
            )
            
            total = filtered_expenses.aggregate(total=Sum('amount'))['total'] or 0
            count = filtered_expenses.count()
            
            category_totals[category_type] = {
                'name': display_name,
                'total': total,
                'count': count
            }
            total_general += total
        
        # Obtener categorías individuales con sus estadísticas
        base_filter = Q(expenses__accounting_year=year)
        if month:
            base_filter &= Q(expenses__accounting_month=month)
        
        categories = ExpenseCategory.objects.filter(is_active=True).annotate(
            total_amount=Sum('expenses__amount', filter=base_filter),
            expense_count=Count('expenses', filter=base_filter)
        ).order_by('category_type', 'name')
        
        context.update({
            'category_totals': category_totals,
            'total_general': total_general,
            'categories': categories,
        })
        
        return context


class ExpenseListView(LoginRequiredMixin, TemporalFilterMixin, CategoryContextMixin, ListView):
    """Lista de gastos filtrada por categoría específica."""
    model = Expense
    template_name = 'expenses/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 25
    
    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        self.category = get_object_or_404(ExpenseCategory, slug=category_slug)
        
        # Obtener filtros temporales usando el mixin
        filters = self.get_temporal_filters()
        expense_filter = filters['expense_filter']
        
        # Construir queryset con filtros por categoría específica
        queryset = Expense.objects.filter(
            category=self.category,
            **expense_filter
        )
            
        return queryset.select_related('category').order_by('-date', '-created')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Total de la categoría actual con filtros aplicados
        context['total_amount'] = self.get_queryset().aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        return context


class ExpenseCreateView(LoginRequiredMixin, CategoryContextMixin, CreateView):
    """Crear un nuevo gasto en una categoría específica."""
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        category_slug = self.kwargs['category_slug']
        self.category = get_object_or_404(ExpenseCategory, slug=category_slug)
        kwargs['category'] = self.category
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('expenses:by-category', kwargs={'category_slug': self.category.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Nuevo Gasto - {self.category.name}'
        return context


class ExpenseUpdateView(LoginRequiredMixin, CategoryContextMixin, UpdateView):
    """Actualizar un gasto existente."""
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        category_slug = self.kwargs['category_slug']
        self.category = get_object_or_404(ExpenseCategory, slug=category_slug)
        kwargs['category'] = self.category
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('expenses:by-category', kwargs={'category_slug': self.category.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Editar Gasto - {self.category.name}'
        return context


class ExpenseDeleteView(LoginRequiredMixin, CategoryContextMixin, DeleteView):
    """Eliminar un gasto."""
    model = Expense
    template_name = 'expenses/expense_confirm_delete.html'
    
    def get_success_url(self):
        category_slug = self.kwargs['category_slug']
        return reverse_lazy('expenses:by-category', kwargs={'category_slug': category_slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(ExpenseCategory, slug=category_slug)
        self.category = category  # Set for CategoryContextMixin
        context.update(self.get_category_context(category))
        return context


class ExpenseCategoryCreateView(LoginRequiredMixin, CreateView):
    """Crear una nueva categoría de gastos."""
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'expenses/category_form.html'
    success_url = reverse_lazy('expenses:categories')
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            SUCCESS_MESSAGES['CATEGORY_CREATED'].format(name=form.instance.name)
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nueva Categoría de Gastos'
        context['submit_text'] = 'Crear Categoría'
        return context


class ExpenseCategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Editar una categoría de gastos existente."""
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'expenses/category_form.html'
    success_url = reverse_lazy('expenses:categories')
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            SUCCESS_MESSAGES['CATEGORY_UPDATED'].format(name=form.instance.name)
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Editar Categoría: {self.object.name}'
        context['submit_text'] = 'Guardar Cambios'
        return context


class ExpenseCategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar una categoría de gastos."""
    model = ExpenseCategory
    template_name = 'expenses/category_confirm_delete.html'
    success_url = reverse_lazy('expenses:categories')
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        category_name = category.name
        
        # Verificar si la categoría tiene gastos asociados
        if category.expenses.exists():
            messages.error(
                request, 
                ERROR_MESSAGES['CATEGORY_HAS_EXPENSES'].format(name=category_name)
            )
            return redirect('expenses:categories')
        
        # Si no tiene gastos, proceder con la eliminación
        result = super().delete(request, *args, **kwargs)
        messages.success(
            request, 
            SUCCESS_MESSAGES['CATEGORY_DELETED'].format(name=category_name)
        )
        return result
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['expense_count'] = self.object.expenses.count()
        return context


class ExpenseCategoryByTypeView(LoginRequiredMixin, TemporalFilterMixin, TemplateView):
    """Vista que muestra categorías filtradas por tipo específico."""
    template_name = 'expenses/categories_by_type.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        category_type = self.kwargs['category_type']
        
        # Validar que el tipo de categoría sea válido
        valid_types = dict(ExpenseCategory.CategoryTypeChoices.choices)
        if category_type not in valid_types:
            raise Http404(ERROR_MESSAGES['INVALID_CATEGORY_TYPE'])
        
        # Obtener filtros temporales usando el mixin
        filters = self.get_temporal_filters()
        expense_filter = filters['expense_filter']
        year = filters['year']
        month = filters['month']
        
        # Obtener categorías del tipo específico con sus estadísticas
        base_filter = Q(expenses__accounting_year=year)
        if month:
            base_filter &= Q(expenses__accounting_month=month)
        
        categories = ExpenseCategory.objects.filter(
            category_type=category_type,
            is_active=True
        ).annotate(
            total_amount=Sum('expenses__amount', filter=base_filter),
            expense_count=Count('expenses', filter=base_filter)
        ).order_by('name')
        
        # Calcular total del tipo específico
        total_amount = Expense.objects.filter(
            category__category_type=category_type,
            **expense_filter
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context.update({
            'category_type': category_type,
            'category_type_display': valid_types[category_type],
            'categories': categories,
            'total_amount': total_amount,
        })
        
        return context
