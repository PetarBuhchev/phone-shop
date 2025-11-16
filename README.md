# Phone Shop - Django E-commerce Application

A modern web shop for selling smartphones built with Django. Features include product management, shopping cart, user authentication, and order history.

## Features

- **Admin Panel**: Add and manage phones with prices, specifications, descriptions, and images
- **Product Listing**: Browse all available smartphones with images, prices, and quick actions
- **Product Details**: View detailed information including specifications and descriptions
- **Shopping Cart**: Add products to cart, update quantities, and remove items
- **User Authentication**: Register, login, and manage user profiles
- **User Profiles**: Save personal information (name, phone, email, address)
- **Order Management**: Place orders and view purchase history
- **Responsive Design**: Modern, mobile-friendly UI

## Installation

1. **Activate the virtual environment** (if not already activated):
   ```bash
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create a superuser** (to access admin panel):
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

6. **Access the application**:
   - Main shop: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Usage

### Adding Products (Admin)

1. Go to http://127.0.0.1:8000/admin/
2. Login with your superuser credentials
3. Navigate to "Products" under "SHOP"
4. Click "Add Product" to add a new smartphone
5. Fill in:
   - Name (e.g., "iPhone 15 Pro")
   - Slug (auto-generated from name)
   - Price
   - Image (upload a product image)
   - Description
   - Specifications (technical details)
   - Stock quantity
   - Available status

### Shopping Flow

1. **Browse Products**: View all available phones on the homepage
2. **View Details**: Click "View" to see full product information
3. **Add to Cart**: Click "Buy" or "Add to Cart" to add items
4. **Manage Cart**: Go to Cart page to update quantities or remove items
5. **Checkout**: Click "Checkout" and fill in shipping information
6. **View Orders**: After placing an order, view it in "My Orders"

### User Account

1. **Register**: Create a new account with username, email, password, and personal info
2. **Login**: Access your account to view orders and manage profile
3. **Profile**: Update your personal information (name, phone, email, address)
4. **Order History**: View all your past purchases

## Project Structure

```
Phone shop/
├── phoneshop/          # Main project settings
│   ├── settings.py     # Django settings
│   ├── urls.py         # Main URL configuration
│   └── ...
├── shop/               # Shop app
│   ├── models.py       # Product and Order models
│   ├── admin.py        # Admin configuration
│   ├── views.py        # Product and order views
│   └── ...
├── cart/               # Shopping cart app
│   ├── cart.py         # Cart session management
│   ├── views.py        # Cart views
│   └── ...
├── accounts/           # User authentication app
│   ├── models.py       # UserProfile model
│   ├── views.py        # Auth views
│   └── ...
├── templates/          # HTML templates
├── media/              # Uploaded images (created automatically)
├── static/             # Static files
└── manage.py           # Django management script
```

## Database Models

- **Product**: Stores phone information (name, price, image, description, specifications)
- **Order**: Stores order information (user, shipping details, status)
- **OrderItem**: Stores individual items in an order
- **UserProfile**: Extends user model with phone and address

## Technologies Used

- Django 4.2.7
- Python 3.x
- SQLite (default database)
- Pillow (for image handling)
- HTML/CSS (responsive design)

## Notes

- The project uses SQLite by default. For production, consider using PostgreSQL or MySQL
- Images are stored in the `media/` directory
- Cart is stored in session, so it persists across page visits
- User authentication is required to view order history
- Admin panel allows full CRUD operations on products

## License

This project is open source and available for educational purposes.

