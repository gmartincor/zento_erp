"""
Tests for accounting module.
TODO: Implementar estrategia de testing profesional al final del proyecto.

Tests pendientes:
- Unit tests para utils (BusinessLineNavigator, ServiceStatisticsCalculator, RemanentesValidator)
- Unit tests para views (todas las vistas jerárquicas)
- Unit tests para models (Client, ClientService)
- Integration tests para flujos completos
- Functional tests para workflows de usuario

Estrategia propuesta:
- Usar pytest + pytest-django
- Fixtures para datos de test
- Mocking para dependencias externas
- Separación por tipos: unit/integration/functional
"""

from django.test import TestCase

# TODO: Implementar tests al final del proyecto


User = get_user_model()


class AccountingViewsTestCase(TestCase):
    """Test cases for accounting views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test user with ADMIN role
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='ADMIN'
        )
        
        # Create test business line hierarchy
        self.root_line = BusinessLine.objects.create(
            name='Test Root',
            slug='test-root',
            level=1,
            is_active=True
        )
        
        self.child_line = BusinessLine.objects.create(
            name='Test Child',
            slug='test-child',
            parent=self.root_line,
            level=2,
            is_active=True
        )
    
    def test_dashboard_view_requires_login(self):
        """Test that dashboard requires authentication."""
        response = self.client.get(reverse('accounting:index'))
        self.assertRedirects(response, '/auth/login/?next=/accounting/')
    
    def test_dashboard_view_with_authenticated_user(self):
        """Test dashboard view with authenticated user."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('accounting:index'))
        self.assertEqual(response.status_code, 200)
    
    def test_business_line_detail_url_pattern(self):
        """Test that business line detail URL pattern works."""
        self.client.login(username='admin', password='testpass123')
        
        # Test single level
        url = reverse('accounting:line-detail', kwargs={'line_path': 'test-root'})
        self.assertEqual(url, '/accounting/test-root/')
        
        # Test two levels
        url = reverse('accounting:line-detail', kwargs={'line_path': 'test-root/test-child'})
        self.assertEqual(url, '/accounting/test-root/test-child/')
    
    def test_service_category_url_pattern(self):
        """Test service category URL pattern."""
        # Test WHITE category
        url = reverse('accounting:category-services', 
                     kwargs={'line_path': 'test-root/test-child', 'category': 'white'})
        self.assertEqual(url, '/accounting/test-root/test-child/white/')
        
        # Test BLACK category
        url = reverse('accounting:category-services', 
                     kwargs={'line_path': 'test-root/test-child', 'category': 'black'})
        self.assertEqual(url, '/accounting/test-root/test-child/black/')


class BusinessLineNavigatorTestCase(TestCase):
    """Test cases for BusinessLineNavigator utility."""
    
    def setUp(self):
        """Set up test business line hierarchy."""
        self.root = BusinessLine.objects.create(
            name='Root',
            slug='root',
            level=1,
            is_active=True
        )
        
        self.child = BusinessLine.objects.create(
            name='Child',
            slug='child',
            parent=self.root,
            level=2,
            is_active=True
        )
        
        self.grandchild = BusinessLine.objects.create(
            name='Grandchild',
            slug='grandchild',
            parent=self.child,
            level=3,
            is_active=True
        )
    
    def test_get_business_line_by_path_single_level(self):
        """Test resolving single level path."""
        result = BusinessLineNavigator.get_business_line_by_path('root')
        self.assertEqual(result, self.root)
    
    def test_get_business_line_by_path_multiple_levels(self):
        """Test resolving multi-level path."""
        result = BusinessLineNavigator.get_business_line_by_path('root/child/grandchild')
        self.assertEqual(result, self.grandchild)
    
    def test_build_line_path(self):
        """Test building path from business line."""
        path = BusinessLineNavigator.build_line_path(self.grandchild)
        self.assertEqual(path, 'root/child/grandchild')
    
    def test_get_business_line_by_path_invalid(self):
        """Test that invalid paths raise appropriate exception."""
        with self.assertRaises(BusinessLine.DoesNotExist):
            BusinessLineNavigator.get_business_line_by_path('invalid/path')


class ServiceStatisticsCalculatorTestCase(TestCase):
    """Test cases for ServiceStatisticsCalculator."""
    
    def setUp(self):
        """Set up test data."""
        self.business_line = BusinessLine.objects.create(
            name='Test Line',
            slug='test-line',
            level=1,
            is_active=True
        )
        
        self.client_obj = AccountingClient.objects.create(
            full_name='Test Client',
            email='test@example.com',
            phone='123456789',
            gender='M'
        )
        
        # Create test services
        self.service_white = ClientService.objects.create(
            client=self.client_obj,
            business_line=self.business_line,
            category='WHITE',
            price=100.00,
            payment_method='CARD'
        )
        
        self.service_black = ClientService.objects.create(
            client=self.client_obj,
            business_line=self.business_line,
            category='BLACK',
            price=200.00,
            payment_method='CASH'
        )
    
    def test_calculate_business_line_stats(self):
        """Test business line statistics calculation."""
        stats = ServiceStatisticsCalculator.calculate_business_line_stats(
            self.business_line, 
            include_children=False
        )
        
        self.assertEqual(stats['total_revenue'], 300.00)
        self.assertEqual(stats['total_services'], 2)
        self.assertEqual(stats['white_services'], 1)
        self.assertEqual(stats['black_services'], 1)
        self.assertEqual(stats['white_revenue'], 100.00)
        self.assertEqual(stats['black_revenue'], 200.00)


# Quick validation function for manual testing
def validate_infrastructure():
    """
    Quick validation function to ensure infrastructure is working.
    Can be called manually to verify everything is set up correctly.
    """
    try:
        # Test imports
        from apps.core.mixins import (
            BusinessLinePermissionMixin,
            BusinessLineHierarchyMixin, 
            ServiceCategoryMixin
        )
        from apps.accounting.utils import (
            BusinessLineNavigator,
            ServiceStatisticsCalculator,
            RemanentesValidator
        )
        from apps.core.constants import (
            ACCOUNTING_SUCCESS_MESSAGES,
            ACCOUNTING_ERROR_MESSAGES,
            SERVICE_CATEGORIES
        )
        
        # Test URL resolution
        from django.urls import reverse
        reverse('accounting:index')
        
        print("✅ All imports successful")
        print("✅ URL patterns working")
        print("✅ Infrastructure validation passed")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


def validate_phase_2():
    """
    Validation function specifically for Phase 2 implementation.
    Tests views, URLs, and basic navigation functionality.
    """
    try:
        # Test view imports
        from apps.accounting.views import (
            AccountingDashboardView,
            BusinessLineDetailView,
            ServiceCategoryListView,
            ServiceEditView,
            ServiceCreateView
        )
        
        # Test URL patterns
        from django.urls import reverse
        
        # Test basic URL patterns
        dashboard_url = reverse('accounting:index')
        assert dashboard_url == '/accounting/'
        
        # Test hierarchical URLs
        line_url = reverse('accounting:line-detail', kwargs={'line_path': 'test'})
        assert line_url == '/accounting/test/'
        
        category_url = reverse('accounting:category-services', 
                              kwargs={'line_path': 'test/child', 'category': 'white'})
        assert category_url == '/accounting/test/child/white/'
        
        print("✅ All views imported successfully")
        print("✅ URL patterns validated")
        print("✅ Hierarchical navigation working")
        print("✅ Phase 2 validation passed")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"❌ URL pattern error: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False
