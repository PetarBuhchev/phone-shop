from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from shop.models import Product, Order, OrderItem
from shop.utils import send_order_confirmation_email
from .cart import Cart
from .forms import CartAddProductForm
from accounts.forms import OrderCreateForm
import logging

logger = logging.getLogger(__name__)


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        
        # Check if product is in stock
        if product.stock == 0:
            messages.error(request, f"Sorry, {product.name} is currently out of stock.")
            return redirect('cart:cart_detail')
        
        # Check if requested quantity is available
        product_id = str(product.id)
        current_cart_quantity = cart.cart.get(product_id, {}).get('quantity', 0)
        total_requested = cd['quantity'] if cd['override'] else current_cart_quantity + cd['quantity']
        
        if total_requested > product.stock:
            messages.error(request, f"Sorry, only {product.stock} units of {product.name} are available.")
            return redirect('cart:cart_detail')
        
        cart.add(product=product,
                 quantity=cd['quantity'],
                 override_quantity=cd['override'])
        logger.info(f"User {request.user} added {cd['quantity']} of product {product.name} to cart")
    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    logger.info(f"User {request.user} removed product {product.name} from cart")
    return redirect('cart:cart_detail')


def cart_detail(request):
    # Admin/staff users shouldn't use the customer cart
    if request.user.is_staff:
        return redirect('shop:product_list')

    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(initial={
            'quantity': item['quantity'],
            'override': True})
    return render(request, 'cart/detail.html', {'cart': cart})


def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            # Check stock availability before creating order
            stock_errors = []
            for item in cart:
                product = item['product']
                if product.stock < item['quantity']:
                    if product.stock == 0:
                        stock_errors.append(f"{product.name} is out of stock.")
                    else:
                        stock_errors.append(f"Only {product.stock} units of {product.name} are available (you requested {item['quantity']}).")
            
            if stock_errors:
                # Add errors to form and redirect back to cart
                for error in stock_errors:
                    form.add_error(None, error)
                return render(request, 'cart/create.html', {'cart': cart, 'form': form})
            
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.save()
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )
                # Update product stock
                item['product'].stock -= item['quantity']
                item['product'].save()
            # clear the cart
            cart.clear()
            logger.info(f"Order {order.id} created by user {request.user} for {cart.get_total_price()}")
            
            # Send order confirmation email
            send_order_confirmation_email(order)
            
            return render(request, 'cart/created.html', {'order': order})
    else:
        if request.user.is_authenticated:
            try:
                profile = request.user.userprofile
                form = OrderCreateForm(initial={
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'email': request.user.email,
                    'phone': profile.phone,
                    'address': profile.address,
                })
            except:
                form = OrderCreateForm(initial={
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'email': request.user.email,
                })
        else:
            form = OrderCreateForm()
    return render(request, 'cart/create.html', {'cart': cart, 'form': form})

