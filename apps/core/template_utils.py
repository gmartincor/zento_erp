class TemplateManager:
    default_template = None
    template_patterns = {}
    
    def get_template_name(self, view_type=None):
        if not view_type:
            return self.default_template
        return self.template_patterns.get(view_type, self.default_template)


class BusinessLineTemplateManager(TemplateManager):
    default_template = 'accounting/business_line_list.html'
    template_patterns = {
        'list': 'accounting/business_line_list.html',
        'detail': 'accounting/business_line_detail.html',
        'form': 'accounting/business_line_form.html',
        'hierarchy': 'accounting/hierarchy_navigation.html',
    }


class ClientTemplateManager(TemplateManager):
    default_template = 'clients/client_list.html'
    template_patterns = {
        'list': 'clients/client_list.html',
        'detail': 'clients/client_detail.html',
        'form': 'clients/client_form.html',
        'history': 'accounting/client_service_history.html',
    }


class ExpenseTemplateManager(TemplateManager):
    default_template = 'expenses/expense_list.html'
    template_patterns = {
        'list': 'expenses/expense_list.html',
        'detail': 'expenses/expense_detail.html',
        'form': 'expenses/expense_form.html',
        'category': 'expenses/category_list.html',
        'category_form': 'expenses/category_form.html',
    }
