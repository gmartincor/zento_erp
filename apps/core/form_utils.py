from django import forms


def apply_currency_field_styles(field, base_class=None):
    if not base_class:
        base_class = ('block w-full px-3 py-2 border border-gray-300 rounded-lg '
                     'focus:ring-2 focus:ring-primary-500 focus:border-primary-500')
    
    currency_class = base_class.replace('px-3', 'pl-8 pr-3')
    
    if isinstance(field.widget, forms.NumberInput):
        field.widget.attrs.update({
            'class': currency_class,
            'step': '0.01',
            'min': '0'
        })


def is_currency_field(field_name):
    return field_name in ['amount', 'price', 'remanente', 'unit_price']
