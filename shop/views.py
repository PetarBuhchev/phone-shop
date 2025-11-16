from django.shortcuts import render, get_object_or_404
from .models import Product, Order, OrderItem
from cart.forms import CartAddProductForm


def product_list(request):
    products = Product.objects.filter(available=True)
    return render(request, 'shop/product/list.html', {'products': products})


def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    cart_product_form = CartAddProductForm()
    return render(request, 'shop/product/detail.html', {
        'product': product,
        'cart_product_form': cart_product_form
    })


def order_history(request):
    if not request.user.is_authenticated:
        return render(request, 'shop/order/history.html', {'orders': []})
    
    orders = Order.objects.filter(user=request.user)
    return render(request, 'shop/order/history.html', {'orders': orders})


def order_detail(request, order_id):
    if not request.user.is_authenticated:
        return render(request, 'shop/order/detail.html', {'order': None})
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order/detail.html', {'order': order})

