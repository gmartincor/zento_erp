from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from apps.business_lines.models import BusinessLine
from apps.accounting.models import Client as AccountingClient, ClientService
from apps.accounting.services.business_line_navigator import BusinessLineNavigator

User = get_user_model()


class AccountingViewsTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='ADMIN'
        )
        
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
        response = self.client.get(reverse('accounting:index'))
        self.assertRedirects(response, '/auth/login/?next=/accounting/')
    
    def test_dashboard_view_with_authenticated_user(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('accounting:index'))
        self.assertEqual(response.status_code, 200)
    
    def test_business_line_detail_url_pattern(self):
        self.client.login(username='admin', password='testpass123')
        
        url = reverse('accounting:line-detail', kwargs={'line_path': 'test-root'})
        self.assertEqual(url, '/accounting/test-root/')
        
        url = reverse('accounting:line-detail', kwargs={'line_path': 'test-root/test-child'})
        self.assertEqual(url, '/accounting/test-root/test-child/')
    
    def test_service_category_url_pattern(self):
        url = reverse('accounting:category-services', 
                     kwargs={'line_path': 'test-root/test-child', 'category': 'personal'})
        self.assertEqual(url, '/accounting/test-root/test-child/personal/')
        
        url = reverse('accounting:category-services', 
                     kwargs={'line_path': 'test-root/test-child', 'category': 'business'})
        self.assertEqual(url, '/accounting/test-root/test-child/business/')


class BusinessLineNavigatorTestCase(TestCase):
    
    def setUp(self):
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
        result = BusinessLineNavigator.get_business_line_by_path('root')
        self.assertEqual(result, self.root)
    
    def test_get_business_line_by_path_multiple_levels(self):
        result = BusinessLineNavigator.get_business_line_by_path('root/child/grandchild')
        self.assertEqual(result, self.grandchild)
    
    def test_build_line_path(self):
        path = BusinessLineNavigator.build_line_path(self.grandchild)
        self.assertEqual(path, 'root/child/grandchild')
    
    def test_get_business_line_by_path_invalid(self):
        with self.assertRaises(BusinessLine.DoesNotExist):
            BusinessLineNavigator.get_business_line_by_path('invalid/path')


class ServiceStatisticsCalculatorTestCase(TestCase):
    
    def setUp(self):
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
        
        self.service_personal = ClientService.objects.create(
            client=self.client_obj,
            business_line=self.business_line,
            category=ClientService.CategoryChoices.PERSONAL,
            price=100.00,
            payment_method='CARD'
        )
        
        self.service_business = ClientService.objects.create(
            client=self.client_obj,
            business_line=self.business_line,
            category=ClientService.CategoryChoices.BUSINESS,
            price=200.00,
            payment_method='CASH'
        )
    
    def test_calculate_business_line_stats(self):
        stats = ServiceStatisticsCalculator.calculate_business_line_stats(
            self.business_line, 
            include_children=False
        )
        
        self.assertEqual(stats['total_revenue'], 300.00)
        self.assertEqual(stats['total_services'], 2)
        self.assertEqual(stats['personal_services'], 1)
        self.assertEqual(stats['business_services'], 1)
        self.assertEqual(stats['personal_revenue'], 100.00)
        self.assertEqual(stats['business_revenue'], 200.00)


def validate_infrastructure():
    try:
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
    try:
        from apps.accounting.views import (
            AccountingDashboardView,
            BusinessLineDetailView,
            ServiceCategoryListView,
            ServiceEditView,
            ServiceCreateView
        )
        
        from django.urls import reverse
        
        dashboard_url = reverse('accounting:index')
        assert dashboard_url == '/accounting/'
        
        line_url = reverse('accounting:line-detail', kwargs={'line_path': 'test'})
        assert line_url == '/accounting/test/'
        
        category_url = reverse('accounting:category-services', 
                              kwargs={'line_path': 'test/child', 'category': 'personal'})
        assert category_url == '/accounting/test/child/personal/'
        
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
