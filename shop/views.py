from django.shortcuts import render, get_object_or_404
from .models import Product, Order, OrderItem
from cart.forms import CartAddProductForm
import logging

logger = logging.getLogger(__name__)

def product_list(request, manufacturer=None):
    if manufacturer:
        products = Product.objects.filter(available=True, manufacturer=manufacturer)
    else:
        products = Product.objects.filter(available=True)
    
    # Get available manufacturers and sort them by display name
    manufacturers_with_names = []
    for code, name in Product.MANUFACTURER_CHOICES:
        if Product.objects.filter(available=True, manufacturer=code).exists():
            manufacturers_with_names.append((code, name))
    
    logger.info(f"User {request.user} accessed product list{' for ' + manufacturer if manufacturer else ''}")
    return render(request, 'shop/product/list.html', {
        'products': products,
        'manufacturers': manufacturers_with_names,
        'current_manufacturer': manufacturer
    })


def product_detail(request, id, slug):
    logger.info(f"User {request.user} viewed product {id} ({slug})")
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    cart_product_form = CartAddProductForm()
    return render(request, 'shop/product/detail.html', {
        'product': product,
        'cart_product_form': cart_product_form
    })


def order_history(request):
    # Only normal (non-staff) users should see customer order history
    if not request.user.is_authenticated or request.user.is_staff:
        return render(request, 'shop/order/history.html', {'orders': []})

    orders = Order.objects.filter(user=request.user)
    return render(request, 'shop/order/history.html', {'orders': orders})


def order_detail(request, order_id):
    # Only normal (non-staff) users should see their order details
    if not request.user.is_authenticated or request.user.is_staff:
        return render(request, 'shop/order/detail.html', {'order': None})

    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order/detail.html', {'order': order})

