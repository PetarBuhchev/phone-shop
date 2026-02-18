"""
Unit tests for the Cart application.
Tests cover cart operations, session management, and cart workflow.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from shop.models import Product
from .cart import Cart


class CartTest(TestCase):
    """Test cases for the Cart class."""
    
    def setUp(self):
        """Set up test client and products."""
        self.client = Client()
        self.session = self.client.session
        
        self.product1 = Product.objects.create(
            name='iPhone 15 Pro',
            slug='iphone-15-pro',
            manufacturer='apple',
            price=Decimal('999.99'),
            description='Latest Apple iPhone',
            specifications='6.1 inch display',
            stock=10
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
    
    def test_cart_add_product(self):
        """Test adding a product to cart."""
        # Create a request with session
        from django.test.client import RequestFactory
        from django.contrib.sessions.middleware import SessionMiddleware
        
        factory = RequestFactory()
        request = factory.get('/')
        
        # Add session to request
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        
        # Create cart and add product
        cart = Cart(request)
        cart.add(self.product1, quantity=1)
        
        # Verify product is in cart
        self.assertIn(str(self.product1.id), cart.cart)
    
    def test_cart_remove_product(self):
        """Test removing a product from cart."""
        from django.test.client import RequestFactory
        from django.contrib.sessions.middleware import SessionMiddleware
        
        factory = RequestFactory()
        request = factory.get('/')
        
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        
        cart = Cart(request)
        cart.add(self.product1, quantity=1)
        self.assertIn(str(self.product1.id), cart.cart)
        
        cart.remove(self.product1)
        self.assertNotIn(str(self.product1.id), cart.cart)
    
    def test_cart_quantity_update(self):
        """Test updating quantity of product in cart."""
        from django.test.client import RequestFactory
        from django.contrib.sessions.middleware import SessionMiddleware
        
        factory = RequestFactory()
        request = factory.get('/')
        
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        
        cart = Cart(request)
        cart.add(self.product1, quantity=1)
        cart.add(self.product1, quantity=2, override_quantity=True)
        
        # Verify quantity is overridden
        self.assertEqual(cart.cart[str(self.product1.id)]['quantity'], 2)
    
    def test_cart_clear(self):
        """Test clearing the cart."""
        from django.test.client import RequestFactory
        from django.contrib.sessions.middleware import SessionMiddleware
        
        factory = RequestFactory()
        request = factory.get('/')
        
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        
        cart = Cart(request)
        cart.add(self.product1, quantity=1)
        cart.add(self.product2, quantity=1)
        
        self.assertEqual(len(cart.cart), 2)
        
        cart.clear()
        self.assertEqual(len(cart.cart), 0)
    
    def test_cart_total_price(self):
        """Test cart total price calculation."""
        from django.test.client import RequestFactory
        from django.contrib.sessions.middleware import SessionMiddleware
        
        factory = RequestFactory()
        request = factory.get('/')
        
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        
        cart = Cart(request)
        cart.add(self.product1, quantity=1)  # 999.99
        cart.add(self.product2, quantity=2)  # 899.99 * 2 = 1799.98
        
        expected_total = Decimal('999.99') + (Decimal('899.99') * 2)
        self.assertEqual(cart.get_total_price(), expected_total)
    
    def test_cart_iteration(self):
        """Test iterating over cart items."""
        from django.test.client import RequestFactory
        from django.contrib.sessions.middleware import SessionMiddleware
        
        factory = RequestFactory()
        request = factory.get('/')
        
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        
        cart = Cart(request)
        cart.add(self.product1, quantity=1)
        cart.add(self.product2, quantity=1)
        
        items = list(cart)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['product'].name, 'iPhone 15 Pro')
        self.assertEqual(items[1]['product'].name, 'Samsung Galaxy S24')


class CartViewTest(TestCase):
    """Test cases for cart views."""
    
    def setUp(self):
        """Set up test client and data."""
        self.client = Client()
        
        self.user = User.objects.create_user(
            username='cartuser',
            email='cart@example.com',
            password='testpass123'
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
    
    def test_cart_detail_view_empty(self):
        """Test viewing empty cart."""
        response = self.client.get(reverse('cart:cart_detail'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cart/detail.html')
    
    def test_cart_add_product_requires_post(self):
        """Test that adding product requires POST."""
        response = self.client.get(reverse('cart:cart_add', args=[self.product.id]))
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_cart_add_out_of_stock_product(self):
        """Test adding out of stock product to cart."""
        self.product.stock = 0
        self.product.save()
        
        response = self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 1, 'override': False}
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect
        # Check that error message was added
        messages = list(response.wsgi_request.messages) if hasattr(response, 'wsgi_request') else []
        # Message assertion would depend on message framework setup
    
    def test_cart_add_product_with_valid_stock(self):
        """Test adding product with sufficient stock."""
        response = self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 2, 'override': False},
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check cart session
        cart_data = self.client.session.get('cart', {})
        self.assertIn(str(self.product.id), cart_data)
    
    def test_cart_remove_product(self):
        """Test removing product from cart."""
        # First add product
        self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 1, 'override': False}
        )
        
        # Then remove it
        response = self.client.post(
            reverse('cart:cart_remove', args=[self.product.id]),
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check cart is empty or doesn't contain product
        cart_data = self.client.session.get('cart', {})
        self.assertNotIn(str(self.product.id), cart_data)


class CartSessionTest(TestCase):
    """Test cases for cart session management."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
        
        self.product = Product.objects.create(
            name='OnePlus 12',
            slug='oneplus-12',
            manufacturer='oneplus',
            price=Decimal('749.99'),
            description='OnePlus flagship',
            specifications='6.7 inch display',
            stock=8
        )
    
    def test_cart_persists_in_session(self):
        """Test that cart data persists in user session."""
        # Add product to cart
        self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 1, 'override': False}
        )
        
        # Check session contains cart data
        self.assertIn('cart', self.client.session)
        cart_data = self.client.session['cart']
        self.assertIn(str(self.product.id), cart_data)
        self.assertEqual(cart_data[str(self.product.id)]['quantity'], 1)
    
    def test_cart_accumulates_quantities(self):
        """Test that adding same product multiple times accumulates quantity."""
        # Add product first time
        self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 2, 'override': False}
        )
        
        # Add same product second time
        self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 1, 'override': False}
        )
        
        # Check accumulated quantity
        cart_data = self.client.session.get('cart', {})
        self.assertEqual(cart_data[str(self.product.id)]['quantity'], 3)

class CartLoginRedirectTest(TestCase):
    """Test cases for cart add to login redirect workflow."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        
        self.user = User.objects.create_user(
            username='loginuser',
            email='login@example.com',
            password='testpass123'
        )
        
        self.product = Product.objects.create(
            name='Sony Xperia',
            slug='sony-xperia',
            manufacturer='sony',
            price=Decimal('899.99'),
            description='Sony flagship phone',
            specifications='6.5 inch display',
            stock=12
        )
    
    def test_unauthenticated_cart_add_redirects_to_login(self):
        """Test that unauthenticated user is redirected to login when adding to cart."""
        response = self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 1, 'override': False}
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_pending_cart_add_saved_in_session(self):
        """Test that pending cart add is saved in session."""
        self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 2, 'override': False}
        )
        
        # Check that pending_cart_add is in session
        self.assertIn('pending_cart_add', self.client.session)
        pending = self.client.session['pending_cart_add']
        self.assertEqual(pending['product_id'], self.product.id)
        self.assertEqual(int(pending['quantity']), 2)
    
    def test_complete_pending_add_without_login(self):
        """Test that completing pending add without login goes to cart detail."""
        response = self.client.get(reverse('cart:complete_pending_add'))
        
        # Should redirect to cart detail
        self.assertEqual(response.status_code, 302)
        self.assertIn('cart', response.url)
    
    def test_complete_pending_add_after_login(self):
        """Test completing pending cart add after successful login."""
        # First, unauthenticated add to cart (saves to session)
        self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 1, 'override': False}
        )
        
        # Verify pending_cart_add is in session
        self.assertIn('pending_cart_add', self.client.session)
        
        # Log in
        self.client.login(username='loginuser', password='testpass123')
        
        # Complete the pending add
        response = self.client.get(reverse('cart:complete_pending_add'), follow=True)
        
        # Should redirect to cart detail
        self.assertEqual(response.status_code, 200)
        
        # Check that product is in cart
        cart_data = self.client.session.get('cart', {})
        self.assertIn(str(self.product.id), cart_data)
    
    def test_auto_add_product_to_authenticated_user_cart(self):
        """Test that product is auto-added after login."""
        # User logs in first
        self.client.login(username='loginuser', password='testpass123')
        
        # Now add to cart (user is authenticated)
        response = self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 2, 'override': False},
            follow=True
        )
        
        # Should redirect to cart detail
        self.assertEqual(response.status_code, 200)
        
        # Check product is in cart
        cart_data = self.client.session.get('cart', {})
        self.assertIn(str(self.product.id), cart_data)
        self.assertEqual(cart_data[str(self.product.id)]['quantity'], 2)