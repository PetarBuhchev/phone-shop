"""
Unit tests for the Shop application.
Tests cover Order and OrderItem models, email functionality, and order workflow.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core import mail
from django.conf import settings
from decimal import Decimal
from .models import Product, Order, OrderItem
from .utils import send_order_confirmation_email, send_order_shipped_email
import logging

logger = logging.getLogger(__name__)


class ProductModelTest(TestCase):
    """Test cases for the Product model."""
    
    def setUp(self):
        """Create test product."""
        self.product = Product.objects.create(
            name='iPhone 15 Pro',
            slug='iphone-15-pro',
            manufacturer='apple',
            price=Decimal('999.99'),
            description='Latest Apple iPhone',
            specifications='6.1 inch display, A17 Pro chip',
            stock=10,
            available=True
        )
    
    def test_product_creation(self):
        """Test that product is created successfully."""
        self.assertEqual(self.product.name, 'iPhone 15 Pro')
        self.assertEqual(self.product.manufacturer, 'apple')
        self.assertEqual(self.product.price, Decimal('999.99'))
        self.assertEqual(self.product.stock, 10)
        self.assertTrue(self.product.available)
    
    def test_product_string_representation(self):
        """Test product __str__ method."""
        self.assertEqual(str(self.product), 'iPhone 15 Pro')
    
    def test_product_absolute_url(self):
        """Test product get_absolute_url method."""
        url = self.product.get_absolute_url()
        self.assertIn(str(self.product.id), url)
        self.assertIn(self.product.slug, url)
    
    def test_product_out_of_stock(self):
        """Test product out of stock status."""
        self.product.stock = 0
        self.product.save()
        self.assertEqual(self.product.stock, 0)
    
    def test_product_slug_unique(self):
        """Test that product slug is unique."""
        with self.assertRaises(Exception):
            Product.objects.create(
                name='iPhone 15',
                slug='iphone-15-pro',  # Duplicate slug
                manufacturer='apple',
                price=Decimal('899.99'),
                description='Another iPhone',
                specifications='5.8 inch display',
                stock=5
            )


class OrderModelTest(TestCase):
    """Test cases for the Order model."""
    
    def setUp(self):
        """Create test order with user and products."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone='1234567890',
            address='123 Main St, City, State 12345',
            status='pending'
        )
        
        self.product1 = Product.objects.create(
            name='iPhone 15 Pro',
            slug='iphone-15-pro',
            manufacturer='apple',
            price=Decimal('999.99'),
            description='Latest Apple iPhone',
            specifications='6.1 inch display',
            stock=20
        )
        
        self.product2 = Product.objects.create(
            name='Samsung Galaxy S24',
            slug='samsung-galaxy-s24',
            manufacturer='samsung',
            price=Decimal('899.99'),
            description='Latest Samsung Phone',
            specifications='6.2 inch display',
            stock=15
        )
    
    def test_order_creation(self):
        """Test that order is created successfully."""
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.first_name, 'John')
        self.assertEqual(self.order.last_name, 'Doe')
        self.assertEqual(self.order.status, 'pending')
        self.assertFalse(self.order.paid)
    
    def test_order_string_representation(self):
        """Test order __str__ method."""
        self.assertEqual(str(self.order), f'Order {self.order.id}')
    
    def test_order_total_cost_empty(self):
        """Test order total cost with no items."""
        total = self.order.get_total_cost()
        self.assertEqual(total, 0)
    
    def test_order_total_cost_with_items(self):
        """Test order total cost calculation with items."""
        OrderItem.objects.create(
            order=self.order,
            product=self.product1,
            price=Decimal('999.99'),
            quantity=1
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product2,
            price=Decimal('899.99'),
            quantity=2
        )
        
        expected_total = Decimal('999.99') + (Decimal('899.99') * 2)
        self.assertEqual(self.order.get_total_cost(), expected_total)
    
    def test_order_status_transitions(self):
        """Test valid order status transitions."""
        self.order.status = 'processing'
        self.order.save()
        self.assertEqual(self.order.status, 'processing')
        
        self.order.status = 'shipped'
        self.order.save()
        self.assertEqual(self.order.status, 'shipped')
        
        self.order.status = 'delivered'
        self.order.save()
        self.assertEqual(self.order.status, 'delivered')
    
    def test_order_mark_as_paid(self):
        """Test marking an order as paid."""
        self.assertFalse(self.order.paid)
        self.order.paid = True
        self.order.save()
        self.assertTrue(self.order.paid)
    
    def test_order_anonymous_user(self):
        """Test creating order without authenticated user."""
        order = Order.objects.create(
            user=None,
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            phone='0987654321',
            address='456 Oak St, Town, State 67890'
        )
        self.assertIsNone(order.user)


class OrderItemModelTest(TestCase):
    """Test cases for the OrderItem model."""
    
    def setUp(self):
        """Create test order item."""
        self.user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            first_name='Alice',
            last_name='Johnson',
            email='alice@example.com',
            phone='5551234567',
            address='789 Pine St'
        )
        
        self.product = Product.objects.create(
            name='Google Pixel 8',
            slug='google-pixel-8',
            manufacturer='google',
            price=Decimal('799.99'),
            description='Google Pixel smartphone',
            specifications='6.2 inch display',
            stock=10
        )
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=Decimal('799.99'),
            quantity=2
        )
    
    def test_order_item_creation(self):
        """Test that order item is created successfully."""
        self.assertEqual(self.order_item.order, self.order)
        self.assertEqual(self.order_item.product, self.product)
        self.assertEqual(self.order_item.price, Decimal('799.99'))
        self.assertEqual(self.order_item.quantity, 2)
    
    def test_order_item_cost(self):
        """Test order item total cost calculation."""
        expected_cost = Decimal('799.99') * 2
        self.assertEqual(self.order_item.get_cost(), expected_cost)
    
    def test_order_item_string_representation(self):
        """Test order item __str__ method."""
        self.assertEqual(str(self.order_item), str(self.order_item.id))
    
    def test_order_item_quantity_update(self):
        """Test updating order item quantity."""
        self.order_item.quantity = 5
        self.order_item.save()
        expected_cost = Decimal('799.99') * 5
        self.assertEqual(self.order_item.get_cost(), expected_cost)


class OrderEmailTest(TestCase):
    """Test cases for order email sending functionality."""
    
    def setUp(self):
        """Create test order for email testing."""
        self.user = User.objects.create_user(
            username='emailtestuser',
            email='emailtest@example.com',
            password='testpass123'
        )
        
        self.order = Order.objects.create(
            user=self.user,
            first_name='Bob',
            last_name='Wilson',
            email='bob@example.com',
            phone='5559876543',
            address='321 Elm St'
        )
        
        self.product = Product.objects.create(
            name='OnePlus 12',
            slug='oneplus-12',
            manufacturer='oneplus',
            price=Decimal('749.99'),
            description='OnePlus flagship',
            specifications='6.7 inch display',
            stock=8
        )
        
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=Decimal('749.99'),
            quantity=1
        )
    
    def test_order_confirmation_email_sent(self):
        """Test that order confirmation email is sent successfully."""
        # Clear the mail outbox
        mail.outbox = []
        
        # Send confirmation email
        result = send_order_confirmation_email(self.order)
        
        # Check that email was sent
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email content
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.order.email])
        self.assertIn('Order Confirmation', email.subject)
        self.assertIn(self.order.first_name, email.body)
    
    def test_order_confirmation_email_html(self):
        """Test that HTML email content is generated."""
        mail.outbox = []
        
        send_order_confirmation_email(self.order)
        
        email = mail.outbox[0]
        # Check that alternative (HTML) is attached
        self.assertTrue(len(email.alternatives) > 0)
        html_content = email.alternatives[0][0]
        self.assertIn('html', html_content.lower() or 'body' in html_content.lower())
    
    def test_order_shipped_email_sent(self):
        """Test that order shipped email is sent successfully."""
        mail.outbox = []
        
        result = send_order_shipped_email(self.order)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.order.email])
        self.assertIn('Shipped', email.subject)
    
    def test_order_shipped_email_with_tracking(self):
        """Test shipped email with tracking number."""
        mail.outbox = []
        tracking_number = 'TRACK123456789'
        
        send_order_shipped_email(self.order, tracking_number=tracking_number)
        
        email = mail.outbox[0]
        self.assertIn(tracking_number, email.body)


class OrderWorkflowTest(TestCase):
    """Integration tests for complete order workflow."""
    
    def setUp(self):
        """Set up test data for workflow testing."""
        self.user = User.objects.create_user(
            username='workflowuser',
            email='workflow@example.com',
            password='testpass123'
        )
        
        self.product = Product.objects.create(
            name='Xiaomi 14',
            slug='xiaomi-14',
            manufacturer='xiaomi',
            price=Decimal('599.99'),
            description='Xiaomi flagship',
            specifications='6.5 inch display',
            stock=5
        )
    
    def test_complete_order_workflow(self):
        """Test complete order workflow from creation to delivery."""
        # Create order
        order = Order.objects.create(
            user=self.user,
            first_name='Charlie',
            last_name='Brown',
            email='charlie@example.com',
            phone='5556789012',
            address='654 Maple Ave'
        )
        
        # Add item to order
        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            price=Decimal('599.99'),
            quantity=2
        )
        
        # Update product stock
        initial_stock = self.product.stock
        self.product.stock -= order_item.quantity
        self.product.save()
        
        # Verify stock was reduced
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock - 2)
        
        # Send confirmation email
        mail.outbox = []
        send_order_confirmation_email(order)
        self.assertEqual(len(mail.outbox), 1)
        
        # Mark as processing
        order.status = 'processing'
        order.save()
        self.assertEqual(order.status, 'processing')
        
        # Mark as shipped
        order.status = 'shipped'
        order.save()
        mail.outbox = []
        send_order_shipped_email(order, tracking_number='SHIPTRACK123')
        self.assertEqual(len(mail.outbox), 1)
        
        # Mark as delivered
        order.status = 'delivered'
        order.save()
        self.assertEqual(order.status, 'delivered')
    
    def test_order_with_multiple_items(self):
        """Test order with multiple different products."""
        product2 = Product.objects.create(
            name='Huawei P60',
            slug='huawei-p60',
            manufacturer='huawei',
            price=Decimal('699.99'),
            description='Huawei flagship',
            specifications='6.3 inch display',
            stock=7
        )
        
        order = Order.objects.create(
            user=self.user,
            first_name='Diana',
            last_name='Prince',
            email='diana@example.com',
            phone='5557890123',
            address='987 Cedar Ln'
        )
        
        # Add multiple items
        item1 = OrderItem.objects.create(
            order=order,
            product=self.product,
            price=Decimal('599.99'),
            quantity=1
        )
        
        item2 = OrderItem.objects.create(
            order=order,
            product=product2,
            price=Decimal('699.99'),
            quantity=1
        )
        
        expected_total = item1.get_cost() + item2.get_cost()
        self.assertEqual(order.get_total_cost(), expected_total)
        
        # Verify order has 2 items
        self.assertEqual(order.items.count(), 2)
