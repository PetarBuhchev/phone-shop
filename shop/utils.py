"""
Email utility functions for the shop app.
Handles sending order confirmation emails with HTML and text templates.
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_order_confirmation_email(order):
    """
    Send order confirmation email to the customer.
    
    Args:
        order: Order object containing order details
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Prepare context for email templates
        context = {
            'order': order,
        }
        
        # Render email subject
        subject = f'Order Confirmation - Order #{order.id}'
        
        # Render text and HTML versions of the email
        text_content = render_to_string('shop/order/email_confirmation.txt', context)
        html_content = render_to_string('shop/order/email_confirmation.html', context)
        
        # Create email message with both text and HTML versions
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Send the email
        email.send(fail_silently=False)
        
        logger.info(f"Order confirmation email sent successfully to {order.email} for order #{order.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation email for order #{order.id}: {str(e)}")
        return False


def send_order_shipped_email(order, tracking_number=None):
    """
    Send order shipped notification email to the customer.
    
    Args:
        order: Order object containing order details
        tracking_number: Optional tracking number for the shipment
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        subject = f'Order Shipped - Order #{order.id}'
        
        tracking_info = f"\nTracking Number: {tracking_number}" if tracking_number else ""
        
        # Simple text-based shipped notification
        text_content = f"""
Order Shipped

Hello {order.first_name} {order.last_name},

Great news! Your order #{order.id} has been shipped and is on its way.{tracking_info}

You can track your order status on our website.

Expected delivery: 5-7 business days from shipment date.

Thank you for your business!

© 2026 Phone Shop. All rights reserved.
"""
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        
        email.send(fail_silently=False)
        
        logger.info(f"Order shipped email sent successfully to {order.email} for order #{order.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order shipped email for order #{order.id}: {str(e)}")
        return False
