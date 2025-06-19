"""
Accounting Views Module - Refactored for Better Architecture

This module now imports all views from organized submodules,
following separation of concerns and maintainability principles.

The original monolithic views.py (1,227 lines) has been split into:
- base.py: Dashboard and base functionality
- business_line.py: Business line management views
- service.py: Client service management views  
- reports.py: Analytics and reporting views

All views are imported here for backward compatibility.
"""

# Import all views from organized modules
from .views.base import AccountingDashboardView
from .views.business_line import (
    BusinessLineDetailView,
    BusinessLineListView,
    BusinessLineHierarchyView
)
from .views.service import (
    ServiceCategoryListView,
    ServiceEditView,
    ServiceCreateView
)
from .views.reports import (
    CategorySummaryView,
    ClientRevenueView
)

# Export all views for URL routing and backward compatibility
__all__ = [
    'AccountingDashboardView',
    'BusinessLineDetailView',
    'BusinessLineListView',
    'BusinessLineHierarchyView', 
    'ServiceCategoryListView',
    'ServiceEditView',
    'ServiceCreateView',
    'CategorySummaryView',
    'ClientRevenueView'
]
