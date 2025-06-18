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


class ExpenseCategoryView(LoginRequiredMixin, TemplateView):
    """Vista principal que muestra categorías de gastos con totales."""
    template_name = 'expenses/categories.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener filtros de fecha desde los parámetros GET
        current_year = timezone.now().year
        current_month = timezone.now().month
        
        year = int(self.request.GET.get('year', current_year))
        month = self.request.GET.get('month')
        
        # Construir el queryset base con filtros temporales
        expense_filter = {'accounting_year': year}
        if month:
            expense_filter['accounting_month'] = int(month)
        
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
            base_filter &= Q(expenses__accounting_month=int(month))
        
        categories = ExpenseCategory.objects.filter(is_active=True).annotate(
            total_amount=Sum('expenses__amount', filter=base_filter),
            expense_count=Count('expenses', filter=base_filter)
        ).order_by('category_type', 'name')
        
        # Crear diccionario de meses para fácil acceso en template
        months_dict = dict([
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ])
        
        context.update({
            'category_totals': category_totals,
            'total_general': total_general,
            'categories': categories,
            'current_year': year,
            'current_month': int(month) if month else None,
            'current_month_name': months_dict.get(int(month)) if month else None,
            'available_years': list(range(2024, current_year + 2)),  # Años disponibles
            'available_months': [
                (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
                (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
                (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
            ]
        })
        
        return context


class ExpenseListView(LoginRequiredMixin, ListView):
    """Lista de gastos filtrada por categoría específica."""
    model = Expense
    template_name = 'expenses/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 25
    
    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        self.category = get_object_or_404(ExpenseCategory, slug=category_slug)
        
        # Filtros temporales de los parámetros GET
        current_year = timezone.now().year
        year = int(self.request.GET.get('year', current_year))
        month = self.request.GET.get('month')
        
        # Construir queryset con filtros por categoría específica
        queryset = Expense.objects.filter(
            category=self.category,
            accounting_year=year
        )
        
        if month:
            queryset = queryset.filter(accounting_month=int(month))
            
        return queryset.select_related('category').order_by('-date', '-created')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtros temporales
        current_year = timezone.now().year
        year = int(self.request.GET.get('year', current_year))
        month = self.request.GET.get('month')
        
        # Información de la categoría actual
        context['category'] = self.category
        context['category_slug'] = self.category.slug
        context['category_display'] = self.category.name
        context['category_type'] = self.category.category_type  # Para retrocompatibilidad en templates
        
        # Total de la categoría actual con filtros aplicados
        context['total_amount'] = self.get_queryset().aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Contexto para filtros temporales
        months_dict = dict([
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ])
        
        context.update({
            'current_year': year,
            'current_month': int(month) if month else None,
            'current_month_name': months_dict.get(int(month)) if month else None,
            'available_years': list(range(2024, current_year + 2)),
            'available_months': [
                (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
                (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
                (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
            ]
        })
        
        return context


class ExpenseCreateView(LoginRequiredMixin, CreateView):
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
        
        context['category'] = self.category
        context['category_slug'] = self.category.slug
        context['category_display'] = self.category.name
        context['category_type'] = self.category.category_type  # Para retrocompatibilidad
        context['form_title'] = f'Nuevo Gasto - {self.category.name}'
        
        return context


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
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
        
        context['category'] = self.category
        context['category_slug'] = self.category.slug
        context['category_display'] = self.category.name
        context['category_type'] = self.category.category_type  # Para retrocompatibilidad
        context['form_title'] = f'Editar Gasto - {self.category.name}'
        
        return context


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
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
        
        context['category'] = category
        context['category_slug'] = category.slug
        context['category_display'] = category.name
        context['category_type'] = category.category_type  # Para retrocompatibilidad
        
        return context


class ExpenseCategoryCreateView(LoginRequiredMixin, CreateView):
    """Crear una nueva categoría de gastos."""
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'expenses/category_form.html'
    success_url = reverse_lazy('expenses:categories')
    
    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{form.instance.name}" creada exitosamente.')
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
        messages.success(self.request, f'Categoría "{form.instance.name}" actualizada exitosamente.')
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
                f'No se puede eliminar la categoría "{category_name}" porque tiene gastos asociados. '
                'Primero debe reasignar o eliminar todos los gastos de esta categoría.'
            )
            return redirect('expenses:categories')
        
        # Si no tiene gastos, proceder con la eliminación
        result = super().delete(request, *args, **kwargs)
        messages.success(request, f'Categoría "{category_name}" eliminada exitosamente.')
        return result
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['expense_count'] = self.object.expenses.count()
        return context


class ExpenseCategoryByTypeView(LoginRequiredMixin, TemplateView):
    """Vista que muestra categorías filtradas por tipo específico."""
    template_name = 'expenses/categories_by_type.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        category_type = self.kwargs['category_type']
        
        # Validar que el tipo de categoría sea válido
        valid_types = dict(ExpenseCategory.CategoryTypeChoices.choices)
        if category_type not in valid_types:
            raise Http404("Tipo de categoría no válido")
        
        # Obtener filtros de fecha desde los parámetros GET
        current_year = timezone.now().year
        current_month = timezone.now().month
        
        year = int(self.request.GET.get('year', current_year))
        month = self.request.GET.get('month')
        
        # Construir el queryset base con filtros temporales
        expense_filter = {'accounting_year': year}
        if month:
            expense_filter['accounting_month'] = int(month)
        
        # Obtener categorías del tipo específico con sus estadísticas
        base_filter = Q(expenses__accounting_year=year)
        if month:
            base_filter &= Q(expenses__accounting_month=int(month))
        
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
        
        # Crear diccionario de meses para fácil acceso en template
        months_dict = dict([
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ])
        
        context.update({
            'category_type': category_type,
            'category_type_display': valid_types[category_type],
            'categories': categories,
            'total_amount': total_amount,
            'current_year': year,
            'current_month': int(month) if month else None,
            'current_month_name': months_dict.get(int(month)) if month else None,
            'available_years': list(range(2024, current_year + 2)),
            'available_months': [
                (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
                (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
                (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
            ]
        })
        
        return context
