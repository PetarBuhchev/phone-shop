"""
Unit tests for the Cart application.
Tests cover cart operations, session management, and cart workflow.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from shop.models import Product


class CartViewTest(TestCase):
    """Test cases for cart views and functionality."""
    
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
        
        self.product2 = Product.objects.create(
            name='iPhone 15 Pro',
            slug='iphone-15-pro',
            manufacturer='apple',
            price=Decimal('999.99'),
            description='Latest Apple iPhone',
            specifications='6.1 inch display',
            stock=5
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
    
    def test_cart_add_product_authenticated(self):
        """Test adding product to cart when authenticated."""
        self.client.login(username='cartuser', password='testpass123')
        
        response = self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 2, 'override': False},
            follow=True
        )
        
        # Should redirect to cart detail
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cart/detail.html')
    
    def test_cart_add_out_of_stock_product(self):
        """Test adding out of stock product to cart."""
        self.client.login(username='cartuser', password='testpass123')
        
        self.product.stock = 0
        self.product.save()
        
        response = self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 1, 'override': False},
            follow=True
        )
        
        # Should show error message and redirect
        self.assertEqual(response.status_code, 200)
    
    def test_cart_add_exceeds_stock(self):
        """Test adding more than available stock."""
        self.client.login(username='cartuser', password='testpass123')
        
        response = self.client.post(
            reverse('cart:cart_add', args=[self.product2.id]),
            {'quantity': 10, 'override': False},
            follow=True
        )
        
        # Should not add more than available
        self.assertEqual(response.status_code, 200)
    
    def test_cart_remove_product(self):
        """Test removing product from cart."""
        self.client.login(username='cartuser', password='testpass123')
        
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
        self.assertTemplateUsed(response, 'cart/detail.html')
    
    def test_unauthenticated_user_redirected_to_login(self):
        """Test that unauthenticated user trying to add to cart is redirected to login."""
        response = self.client.post(
            reverse('cart:cart_add', args=[self.product.id]),
            {'quantity': 1, 'override': False}
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_pending_cart_add_in_session_after_unauthenticated_add(self):
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
        """Test that completing pending add without login redirects to cart."""
        response = self.client.get(reverse('cart:complete_pending_add'))
        
        # Should redirect to cart detail
        self.assertEqual(response.status_code, 302)
        self.assertIn('cart', response.url)


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