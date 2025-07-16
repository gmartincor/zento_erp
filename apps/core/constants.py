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

DEFAULT_START_YEAR = 2024
FINANCIAL_YEAR_BUFFER = 3

DEFAULT_PAGINATION = 25

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
    'INVALID_SERVICE_CATEGORY': 'Categoría de servicio "{category}" no válida. Debe ser PERSONAL o BUSINESS.',
    'REMANENTE_NOT_ALLOWED': 'Los remanentes no están permitidos para la línea de negocio "{name}".',
    'INVALID_REMANENTE_FIELD': 'Campo de remanente "{field}" no válido para la línea "{name}".',
    'CLIENT_HAS_ACTIVE_SERVICES': (
        'No se puede eliminar el cliente "{name}" porque tiene servicios activos. '
        'Primero debe desactivar o eliminar todos los servicios asociados.'
    ),
    'DUPLICATE_SERVICE': 'Ya existe un servicio de categoría "{category}" para este cliente en esta línea de negocio.',
}

ACCOUNTING_URL_PATTERNS = {
    'INDEX': 'accounting:index',
    'LINE_DETAIL': 'accounting:business-lines-path',
    'PERSONAL_SERVICES': 'accounting:personal-services',
    'BUSINESS_SERVICES': 'accounting:business-services',
    'SERVICE_CREATE': 'accounting:service-create',
    'SERVICE_EDIT': 'accounting:service-edit',
    'SERVICE_DELETE': 'accounting:service-delete',
    'CLIENT_CREATE': 'accounting:client-create',
    'CLIENT_EDIT': 'accounting:client-edit',
}

SERVICE_CATEGORIES = {
    'PERSONAL': 'personal',
    'BUSINESS': 'business',
}

SERVICE_CATEGORY_DISPLAY = {
    'PERSONAL': 'Servicios Personal',
    'BUSINESS': 'Servicios Business',
}

EXPENSE_SERVICE_CATEGORIES = {
    'PERSONAL': 'personal',
    'BUSINESS': 'business',
    'SHARED': 'shared',
}

EXPENSE_SERVICE_CATEGORY_DISPLAY = {
    'PERSONAL': 'Personal',
    'BUSINESS': 'Business',
    'SHARED': 'Compartido',
}

PAYMENT_METHOD_DISPLAY = {
    'CARD': 'Tarjeta',
    'CASH': 'Efectivo',
    'TRANSFER': 'Transferencia',
    'BIZUM': 'Bizum',
}

GENDER_DISPLAY = {
    'M': 'Masculino',
    'F': 'Femenino',
    'O': 'Otro',
}

BUSINESS_LINE_LEVELS = {
    'LEVEL_1': 1,
    'LEVEL_2': 2,
    'LEVEL_3': 3,
}

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

CATEGORY_CONFIG = {
    'personal': {
        'name': 'Servicio Personal',
        'color': 'green',
        'icon': 'check-circle',
        'badge_class': 'bg-blue-100 text-blue-800',
        'bg_class': 'bg-emerald-100 dark:bg-emerald-900',
        'text_class': 'text-emerald-600 dark:text-emerald-300'
    },
    'business': {
        'name': 'Servicio Business',
        'color': 'purple',
        'icon': 'exclamation-circle',
        'badge_class': 'bg-gray-100 text-gray-800',
        'bg_class': 'bg-purple-100 dark:bg-purple-900',
        'text_class': 'text-purple-600 dark:text-purple-300'
    }
}

CATEGORY_DEFAULTS = {
    'DEFAULT_CATEGORY': 'personal',
    'VALID_CATEGORIES': ['personal', 'business']
}

TENANT_SUCCESS_MESSAGES = {
    'TENANT_CREATED': 'Cuenta de nutricionista "{name}" creada exitosamente.',
    'TENANT_UPDATED': 'Cuenta de nutricionista "{name}" actualizada exitosamente.',
    'TENANT_ACTIVATED': 'Cuenta de nutricionista "{name}" activada exitosamente.',
    'TENANT_DEACTIVATED': 'Cuenta de "{name}" desactivada exitosamente.',
    'TENANT_SUSPENDED': 'Cuenta de nutricionista "{name}" suspendida.',
    'TENANT_DELETED': 'Cuenta de nutricionista "{name}" eliminada exitosamente.',
}

TENANT_ERROR_MESSAGES = {
    'EMAIL_EXISTS': 'Ya existe una cuenta con el email "{email}".',
    'TENANT_NOT_FOUND': 'Nutricionista no encontrado.',
    'TENANT_INACTIVE': 'La cuenta está desactivada.',
    'TENANT_SUSPENDED': 'La cuenta está suspendida.',
    'SCHEMA_CREATION_FAILED': 'Error al crear el esquema de base de datos.',
}
