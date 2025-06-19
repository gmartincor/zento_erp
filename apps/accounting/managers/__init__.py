"""
Managers package for complex database queries.

This package contains custom managers for optimized database operations
and complex queries that are reused across the accounting module.
"""

from .client_service_manager import ClientServiceManager
from .business_line_manager import BusinessLineManager

__all__ = [
    'ClientServiceManager',
    'BusinessLineManager'
]
