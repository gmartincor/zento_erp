"""
Accounting Views Module

Organizes all views into separate files based on functionality following
the separation of concerns principle.
"""

# Import views from reorganized modules
from .base import AccountingDashboardView
from .business_line import (
    BusinessLineListView,
    BusinessLineHierarchyView
)
from .service import (
    ServiceCategoryListView,
    ServiceEditView,
    ServiceCreateView
)
from .reports import (
    CategorySummaryView,
    ClientRevenueView
)

# Export all views for backward compatibility
__all__ = [
    'AccountingDashboardView',
    'BusinessLineDetailView',
    'BusinessLineListView', 
    'BusinessLineHierarchyView',
    'ServiceCategoryListView',
    'ServiceEditView',
    'ServiceCreateView',
    'CategorySummaryView',
    'ClientRevenueView',
]
