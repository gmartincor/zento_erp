"""
Constants for the CRM Nutrition Pro application.
Centralized constants to avoid code duplication and ensure consistency.
"""

# Date and Time Constants
MONTHS_DICT = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

MONTHS_CHOICES = [
    (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
    (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
    (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
]

# Default date range for financial reports
DEFAULT_START_YEAR = 2024
FINANCIAL_YEAR_RANGE_EXTENSION = 2  # Years to extend beyond current year

# Pagination defaults
DEFAULT_PAGINATION = 25

# Message types and common messages
SUCCESS_MESSAGES = {
    'CATEGORY_CREATED': 'Categoría "{name}" creada exitosamente.',
    'CATEGORY_UPDATED': 'Categoría "{name}" actualizada exitosamente.',
    'CATEGORY_DELETED': 'Categoría "{name}" eliminada exitosamente.',
    'EXPENSE_CREATED': 'Gasto registrado exitosamente.',
    'EXPENSE_UPDATED': 'Gasto actualizado exitosamente.',
    'EXPENSE_DELETED': 'Gasto eliminado exitosamente.',
}

ERROR_MESSAGES = {
    'CATEGORY_HAS_EXPENSES': (
        'No se puede eliminar la categoría "{name}" porque tiene gastos asociados. '
        'Primero debe reasignar o eliminar todos los gastos de esta categoría.'
    ),
    'INVALID_CATEGORY_TYPE': 'Tipo de categoría no válido',
}

# Accounting module constants
ACCOUNTING_SUCCESS_MESSAGES = {
    'CLIENT_CREATED': 'Cliente "{name}" creado exitosamente.',
    'CLIENT_UPDATED': 'Cliente "{name}" actualizado exitosamente.',
    'CLIENT_DELETED': 'Cliente "{name}" eliminado exitosamente.',
    'SERVICE_CREATED': 'Servicio para "{client}" creado exitosamente.',
    'SERVICE_UPDATED': 'Servicio actualizado exitosamente.',
    'SERVICE_DELETED': 'Servicio eliminado exitosamente.',
    'REMANENTE_UPDATED': 'Remanente actualizado exitosamente.',
}

ACCOUNTING_ERROR_MESSAGES = {
    'INVALID_BUSINESS_LINE_PATH': 'La ruta de línea de negocio "{path}" no es válida.',
    'BUSINESS_LINE_NOT_FOUND': 'Línea de negocio "{name}" no encontrada.',
    'PERMISSION_DENIED_BUSINESS_LINE': 'No tienes permisos para acceder a la línea de negocio "{name}".',
    'INVALID_SERVICE_CATEGORY': 'Categoría de servicio "{category}" no válida. Debe ser WHITE o BLACK.',
    'REMANENTE_NOT_ALLOWED': 'Los remanentes no están permitidos para la línea de negocio "{name}".',
    'INVALID_REMANENTE_FIELD': 'Campo de remanente "{field}" no válido para la línea "{name}".',
    'CLIENT_HAS_ACTIVE_SERVICES': (
        'No se puede eliminar el cliente "{name}" porque tiene servicios activos. '
        'Primero debe desactivar o eliminar todos los servicios asociados.'
    ),
    'DUPLICATE_SERVICE': 'Ya existe un servicio de categoría "{category}" para este cliente en esta línea de negocio.',
}

# URL pattern constants for accounting
ACCOUNTING_URL_PATTERNS = {
    'INDEX': 'accounting:index',
    'LINE_DETAIL': 'accounting:business-lines-path',
    'WHITE_SERVICES': 'accounting:white-services',
    'BLACK_SERVICES': 'accounting:black-services',
    'SERVICE_CREATE': 'accounting:service-create',
    'SERVICE_EDIT': 'accounting:service-edit',
    'SERVICE_DELETE': 'accounting:service-delete',
    'CLIENT_CREATE': 'accounting:client-create',
    'CLIENT_EDIT': 'accounting:client-edit',
}

# Service categories
SERVICE_CATEGORIES = {
    'WHITE': 'WHITE',
    'BLACK': 'BLACK',
}

SERVICE_CATEGORY_DISPLAY = {
    'WHITE': 'Servicios White',
    'BLACK': 'Servicios Black',
}

# Payment method display names
PAYMENT_METHOD_DISPLAY = {
    'CARD': 'Tarjeta',
    'CASH': 'Efectivo',
    'TRANSFER': 'Transferencia',
    'BIZUM': 'Bizum',
}

# Gender display names
GENDER_DISPLAY = {
    'M': 'Masculino',
    'F': 'Femenino',
    'O': 'Otro',
}

# Business line level constants
BUSINESS_LINE_LEVELS = {
    'LEVEL_1': 1,
    'LEVEL_2': 2,
    'LEVEL_3': 3,
}

# Navigation constants
NAVIGATION_ITEMS = {
    'ACCOUNTING': {
        'name': 'Ingresos',
        'icon': 'currency-dollar',
        'subitems': [
            {'name': 'Por Línea de Negocio', 'url': 'accounting:index'},
            {'name': 'Por Categoría', 'url': 'accounting:by-category'},
            {'name': 'Por Cliente', 'url': 'accounting:by-client'},
        ]
    }
}
