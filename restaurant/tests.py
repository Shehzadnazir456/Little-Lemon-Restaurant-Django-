"""
Tests for the Little Lemon restaurant app.

Run with:
    python manage.py test restaurant

Coverage:
  - Menu list view
  - Reservation form submission (valid + invalid)
  - Order creation: dine-in and takeaway paths
  - Dashboard redirect for unauthenticated users
  - Order status lookup
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from .models import Category, MenuItem, Order, OrderItem, Reservation


User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_category(name='Starters', slug='starters'):
    return Category.objects.get_or_create(name=name, slug=slug, defaults={'order': 1})[0]


def make_menu_item(name='Greek Salad', price='8.50', category=None):
    if category is None:
        category = make_category()
    return MenuItem.objects.get_or_create(
        name=name,
        defaults={
            'description': 'A test menu item.',
            'price': Decimal(price),
            'category': category,
        }
    )[0]


# ---------------------------------------------------------------------------
# Menu tests
# ---------------------------------------------------------------------------

class MenuViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.cat = make_category()
        make_menu_item('Greek Salad', '8.50', self.cat)
        make_menu_item('Bruschetta', '7.00', self.cat)

    def test_menu_page_returns_200(self):
        response = self.client.get(reverse('menu'))
        self.assertEqual(response.status_code, 200)

    def test_menu_page_contains_items(self):
        response = self.client.get(reverse('menu'))
        self.assertContains(response, 'Greek Salad')
        self.assertContains(response, 'Bruschetta')

    def test_menu_filter_by_category(self):
        other_cat = make_category('Desserts', 'desserts')
        make_menu_item('Baklava', '7.00', other_cat)
        url = reverse('menu') + '?category=starters'
        response = self.client.get(url)
        self.assertContains(response, 'Greek Salad')
        self.assertNotContains(response, 'Baklava')


# ---------------------------------------------------------------------------
# Reservation tests
# ---------------------------------------------------------------------------

class ReservationFormTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('reservation')

    def test_reservation_page_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_valid_reservation_created(self):
        data = {
            'name':    'Alice Smith',
            'email':   'alice@example.com',
            'contact': '03001234567',
            'time':    '2027-12-25T19:00',
            'count':   4,
            'notes':   'Window seat please.',
        }
        response = self.client.post(self.url, data)
        # Should redirect after success
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Reservation.objects.filter(name='Alice Smith').exists())

    def test_invalid_reservation_missing_required_fields(self):
        response = self.client.post(self.url, {'name': '', 'contact': '', 'count': ''})
        self.assertEqual(response.status_code, 200)  # re-render with errors
        self.assertFalse(Reservation.objects.filter(name='').exists())


# ---------------------------------------------------------------------------
# Order tests
# ---------------------------------------------------------------------------

class OrderCreationTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.cat = make_category()
        self.item = make_menu_item('Lamb Chops', '24.00', self.cat)
        # Populate session cart
        session = self.client.session
        session['cart'] = {str(self.item.pk): 2}
        session.save()

    def test_checkout_page_returns_200_with_cart(self):
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 200)

    def test_checkout_empty_cart_redirects(self):
        # Clear cart
        session = self.client.session
        session['cart'] = {}
        session.save()
        response = self.client.get(reverse('checkout'))
        self.assertRedirects(response, reverse('menu'))

    def test_dine_in_order_created(self):
        data = {
            'customer_name': 'Bob Jones',
            'email':         'bob@example.com',
            'phone':         '03009876543',
            'order_type':    'dine_in',
            'party_size':    3,
            'notes':         '',
            'delivery_address': '',
        }
        response = self.client.post(reverse('checkout'), data)
        self.assertEqual(response.status_code, 302)
        order = Order.objects.filter(customer_name='Bob Jones').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.order_type, 'dine_in')
        # Total = 24.00 * 2
        self.assertEqual(order.total_price, Decimal('48.00'))
        self.assertEqual(order.order_items.count(), 1)

    def test_takeaway_order_requires_address(self):
        data = {
            'customer_name': 'Carol White',
            'email':         'carol@example.com',
            'phone':         '',
            'order_type':    'takeaway',
            'delivery_address': '',  # missing — should fail
            'party_size':    '',
            'notes':         '',
        }
        response = self.client.post(reverse('checkout'), data)
        self.assertEqual(response.status_code, 200)  # re-render with errors
        self.assertFalse(Order.objects.filter(customer_name='Carol White').exists())

    def test_takeaway_order_created_with_address(self):
        data = {
            'customer_name':    'Carol White',
            'email':            'carol@example.com',
            'phone':            '',
            'order_type':       'takeaway',
            'delivery_address': '123 Main Street, Islamabad',
            'party_size':       '',
            'notes':            '',
        }
        response = self.client.post(reverse('checkout'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Order.objects.filter(customer_name='Carol White').exists())


# ---------------------------------------------------------------------------
# Dashboard auth tests
# ---------------------------------------------------------------------------

class DashboardAuthTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass123', is_staff=True
        )
        self.normal_user = User.objects.create_user(
            username='normaluser', password='testpass123', is_staff=False
        )

    def test_dashboard_redirects_unauthenticated(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin-login/', response['Location'])

    def test_dashboard_redirects_non_staff(self):
        self.client.login(username='normaluser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_accessible_to_staff(self):
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_orders_redirects_unauthenticated(self):
        response = self.client.get(reverse('dashboard_orders'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_reservations_redirects_unauthenticated(self):
        response = self.client.get(reverse('dashboard_reservations'))
        self.assertEqual(response.status_code, 302)


# ---------------------------------------------------------------------------
# Order status lookup tests
# ---------------------------------------------------------------------------

class OrderStatusTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.order = Order.objects.create(
            customer_name='Dave Brown',
            email='dave@example.com',
            order_type='dine_in',
            party_size=2,
            total_price=Decimal('16.00'),
        )

    def test_order_status_page_returns_200(self):
        response = self.client.get(reverse('order_status'))
        self.assertEqual(response.status_code, 200)

    def test_valid_lookup_shows_order(self):
        url = reverse('order_status') + f'?order_id={self.order.pk}&email=dave@example.com'
        response = self.client.get(url)
        self.assertContains(response, 'Dave Brown')

    def test_wrong_email_shows_error(self):
        url = reverse('order_status') + f'?order_id={self.order.pk}&email=wrong@example.com'
        response = self.client.get(url)
        self.assertNotContains(response, 'Dave Brown')
