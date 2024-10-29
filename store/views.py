from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .forms import UserRegistrationForm, SellerRegistrationForm
from django.contrib.auth.decorators import user_passes_test
from .models import *
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models.functions import TruncMonth
from django.db.models import Sum, Count
from .forms import *
# User registration view
def register_user(request):
    form = UserRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()  # Normal users are active by default, no need to set is_active here
        return redirect('user_login')  # Redirect to login after successful registration
    return render(request, 'store/register_user.html', {'form': form})

# Seller registration view
def register_seller(request):
    if request.method == 'POST':
        form = SellerRegistrationForm(request.POST)
        if form.is_valid():
            # Save the seller (user) but don't commit it to the database yet
            seller = form.save(commit=False)
            seller.is_seller = True  # Mark as a seller
            seller.is_active = False  # Set the seller to inactive initially
            seller.save()  # Save the seller to the database

            # Create the seller profile
            SellerProfile.objects.create(
                user=seller,
                name=request.POST.get('name'),
                business_name=request.POST.get('business_name'),
                tax_info=request.POST.get('tax_info'),
                location=request.POST.get('location'),
                address=request.POST.get('address'),
            )

            return redirect('user_login')  # Redirect after successful registration
    else:
        form = SellerRegistrationForm()

    return render(request, 'store/register_seller.html', {'form': form})


# User login view
def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)

        if user:
            login(request, user)
            # Redirect based on the user's role
            if user.is_admin:  # Check if the user is an admin
                return redirect('admin_dashboard')  # Redirect to admin dashboard
            elif user.is_seller:  # Check if the user is a seller
                return redirect('seller_dashboard')  # Redirect to seller dashboard
            else:
                return redirect('home')  # Redirect regular users to home page
        else:
            return render(request, 'store/login.html', {'error': 'Invalid login credentials'})  # Handle login failure

    return render(request, 'store/login.html')



# Home view (for regular users)
def home(request):
    products = Product.objects.filter(status=True)  # Fetch only active products
    return render(request, 'store/home.html', {'products': products})


# Admin dashboard view, accessible only to admin users
import json
@user_passes_test(lambda u: u.is_admin)
def admin_dashboard(request):
    # Existing statistics
    total_sales = Order.objects.aggregate(total=Sum('total_price'))['total'] or 0
    order_count = Order.objects.count()
    seller_count =  User.objects.filter(is_seller=True).count(),
    category_count = Category.objects.count()
    pending_settlement_count = SettlementRequest.objects.filter(status='pending').count()
    product_count = Product.objects.count()
    recent_orders = Order.objects.order_by('-created_at')[:5]

    # Monthly sales data
    monthly_sales = Order.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(total_sales=Sum('total_price')).order_by('month')
    monthly_sales_data = [
        {
            'month': sale['month'].strftime("%B %Y"),
            'total_sales': float(sale['total_sales'])
        } for sale in monthly_sales
    ]

    # Top selling categories data
    top_categories = Category.objects.annotate(total_sales=Sum('products__orderitem__order__total_price')).order_by('-total_sales')[:5]
    top_categories_data = [
        {
            'category': category.name,
            'total_sales': float(category.total_sales or 0)
        } for category in top_categories
    ]

    # Order status distribution data
    order_status = Order.objects.values('status').annotate(count=Count('id'))
    order_status_data = [
        {
            'status': status['status'],
            'count': status['count']
        } for status in order_status
    ]

    # Debug output
    print("Monthly Sales Data:", monthly_sales_data)
    print("Top Categories Data:", top_categories_data)
    print("Order Status Data:", order_status_data)

    context = {
        'total_sales': total_sales,
        'order_count': order_count,
        'seller_count': seller_count,
        'category_count': category_count,
        'pending_settlement_count': pending_settlement_count,
        'product_count': product_count,
        'recent_orders': recent_orders,
        'monthly_sales_data': json.dumps(monthly_sales_data),
        'top_categories_data': json.dumps(top_categories_data),
        'order_status_data': json.dumps(order_status_data),
    }
    return render(request, 'store/admin_dashboard.html', context)



@user_passes_test(lambda u: u.is_admin)
def settlement_requests_list_admin(request):
    settlement_requests = SettlementRequest.objects.all().order_by('-requested_at')
    return render(request, 'store/admin_settlement_request.html', {'settlement_requests': settlement_requests})

@user_passes_test(lambda u: u.is_admin)
def settlement_request_detail(request, request_id):
    settlement_request = get_object_or_404(SettlementRequest, id=request_id)
    return render(request, 'store/settlement_request_detail_admin.html', {'settlement_request': settlement_request})

@user_passes_test(lambda u: u.is_admin)
def update_settlement_request_admin(request, request_id):
    settlement_request = get_object_or_404(SettlementRequest, id=request_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        admin_comment = request.POST.get('admin_comment')
        settlement_request.status = status
        settlement_request.admin_comment = admin_comment
        settlement_request.save()
    return redirect('settlement_requests_list_admin')

# Admin login view
def admin_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)

        if user and user.is_admin:  # Ensure that the user is an admin
            login(request, user)
            return redirect('admin_dashboard')  # Redirect to the admin dashboard after login
        else:
            return render(request, 'store/admin_login.html', {'error': 'Invalid credentials or not an admin user'})
    
    return render(request, 'store/admin_login.html')

# Admin logout view
def admin_logout(request):
    logout(request)  # This will log out the user
    return redirect('admin_login')  # Redirect to the admin login page after logout



@user_passes_test(lambda u: u.is_seller)
def seller_dashboard(request):
    context = {
        'total_orders': Order.objects.filter(items__product__created_by=request.user).distinct().count(),
        'total_products': Product.objects.filter(created_by=request.user).count(),
        'total_revenue': Order.objects.filter(items__product__created_by=request.user).aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'recent_orders': Order.objects.filter(items__product__created_by=request.user).distinct().order_by('-created_at')[:5],
        'settlement_requests': SettlementRequest.objects.filter(seller=request.user).order_by('-requested_at')[:5],
    }
    return render(request, 'store/seller_dashboard.html', context)

@login_required
def list_sellers(request):
    if not request.user.is_superuser:
        raise PermissionDenied  # Raise 403 Forbidden if the user is not a superuser
    
    print("Inside list_sellers view")
    sellers = User.objects.filter(is_seller=True)
    print(f"Number of sellers: {sellers.count()}")
    return render(request, 'store/admin_sellers.html', {'sellers': sellers})


@user_passes_test(lambda u: u.is_admin)
def delete_seller(request, seller_id):
    seller = get_object_or_404(User, id=seller_id, is_seller=True)

    if request.method == 'POST':
        seller.delete()  # Deletes the seller from the database
        return redirect('admin_sellers')  # Redirect back to the seller list after deletion

    return render(request, 'store/admin_delete_seller.html', {'seller': seller})

@user_passes_test(lambda u: u.is_admin)
def approve_seller(request, seller_id):
    # Get the seller to be approved (inactive seller)
    seller = get_object_or_404(User, id=seller_id, is_seller=True, is_active=False)

    if request.method == 'POST':
        # Update seller's status to active
        seller.is_active = True
        seller.save()
        return redirect('admin_sellers')  # Redirect to seller list after approval

    # Render the template showing seller details and an approval button
    return render(request, 'store/admin_approve_seller.html', {'seller': seller})



# Check if the user is an admin
@user_passes_test(lambda u: u.is_admin)
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'store/category_list.html', {'categories': categories})

@user_passes_test(lambda u: u.is_admin)
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm()

    return render(request, 'store/add_category.html', {'form': form})

@user_passes_test(lambda u: u.is_admin)
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'store/edit_category.html', {'form': form, 'category': category})




@user_passes_test(lambda u: u.is_admin)
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')  # Redirect to the category list after deletion

    return redirect('edit_category', category_id=category.id)  # If method is not POST




@login_required
def user_logout(request):
    """Log out the current user and redirect to the common login page."""
    logout(request)  # This logs out the current user
    return redirect('user_login')  # Redirect to the login page after logout


@login_required
def list_products(request):
    search_query = request.GET.get('search', '')
    
    # Filter products based on search query
    if search_query:
        products = Product.objects.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query),
            created_by=request.user
        )
    else:
        products = Product.objects.filter(created_by=request.user)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 10)  # Show 10 products per page
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        'products': products,
        'search_query': search_query,
    }
    
    return render(request, 'store/seller_product_list.html', context)
@login_required
@user_passes_test(lambda u: u.is_seller)
def add_product(request):
    if request.method == 'POST':
        print("POST request received")  # Debug: Check if POST request is received
        print("Request.POST:", request.POST)  # Debug: Print the POST data
        print("Request.FILES:", request.FILES)  # Debug: Print the FILES data

        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            print("Form is valid")  # Debug: Form validation passed

            # Save the product but don't commit to the database yet
            product = form.save(commit=False)
            product.created_by = request.user  # Assign the current user as the seller
            
            product.status = True
            product.save()  # Save the product to the database

            print(f"Product '{product.name}' created by {request.user}")  # Debug: Product created successfully
            return redirect('list_products')  # Redirect to the product list page
        else:
            print("Form errors:", form.errors)  # Debug: Form validation failed, print errors
    else:
        print("GET request received")  # Debug: Check if GET request is received
        form = ProductForm()

    return render(request, 'store/seller_add_product.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_seller)
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, created_by=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('list_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'store/edit_product.html', {'form': form, 'product': product})




@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check if the user has purchased this product
    order_items = OrderItem.objects.filter(product=product, order__user=request.user)
    if not order_items.exists():
        return render(request, 'store/error.html', {'message': 'You can only review products you have purchased.'})

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            order_item = order_items.first()  # Assuming the user can only purchase the product once
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.order_item = order_item  # Link review to the purchased order item
            review.save()
            return redirect('product_detail', product_id=product.id)
    else:
        form = ReviewForm()

    return render(request, 'store/add_review.html', {'form': form, 'product': product})





def product_list(request):
    products = Product.objects.filter(status=True)  # Show only active products
    return render(request, 'store/product_list.html', {'products': products})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Category, Review, OrderItem

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all()
    related_products = product.related_products.all()
    categories = Category.objects.all()

    # Get product rating as a range for displaying stars
    product_rating = round(product.average_rating())  # Round to nearest integer for displaying stars
    rating_range = range(product_rating)

    # Check if the user can submit a review
    can_review = False
    if request.user.is_authenticated:
        order_items = OrderItem.objects.filter(product=product, order__user=request.user)
        if order_items.exists() and not product.reviews.filter(user=request.user).exists():
            can_review = True

    if request.method == 'POST' and can_review:
        rating = int(request.POST.get('rating', 5))
        comment = request.POST.get('review')
        review, created = Review.objects.get_or_create(
            user=request.user, product=product, order_item=order_items.first())
        review.rating = rating
        review.comment = comment
        review.save()
        return redirect('product_detail', product_id=product.id)

    context = {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'categories': categories,
        'rating_range': rating_range,
        'can_review': can_review,
    }
    return render(request, 'store/product_detail.html', context)

def list_products_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    return render(request, 'store/product_list.html', {
        'category': category,
        'products': products,
    })

@login_required
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Ensure that the user has purchased the product before reviewing
    order_items = OrderItem.objects.filter(product=product, order__user=request.user)
    if not order_items.exists():
        messages.error(request, "You need to purchase the product before reviewing.")
        return redirect('product_detail', product_id=product.id)

    # Check if the user has already reviewed the product
    if product.reviews.filter(user=request.user).exists():
        messages.error(request, "You have already reviewed this product.")
        return redirect('product_detail', product_id=product.id)

    if request.method == 'POST':
        review_text = request.POST.get('review')
        rating = request.POST.get('rating')

        # Validate rating to ensure it's between 1 and 5
        if not rating or int(rating) < 1 or int(rating) > 5:
            messages.error(request, "Please provide a valid rating between 1 and 5.")
            return redirect('product_detail', product_id=product.id)

        # Save the review
        review = Review.objects.create(
            product=product,
            user=request.user,
            rating=int(rating),
            comment=review_text
        )
        review.save()

        messages.success(request, "Thank you for your review!")
        return redirect('product_detail', product_id=product.id)

    return render(request, 'store/product_detail.html', {
        'product': product
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Get or create a cart item for the user
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('view_cart')

@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = 0
    total_shipping = 0
    total_tax = 0
    total_discount = 0
    
    for item in cart_items:
        product = item.product
        base_price = product.price
        shipping = product.shipping_charge
        tax_rate = product.tax_percentage  # Update to use tax_percentage instead of tax_rate
        offer = product.discount or 0

        # Calculate discounted price
        discounted_price = base_price - (base_price * offer / 100)

        # Calculate tax
        tax_amount = discounted_price * tax_rate / 100

        # Calculate total price for the item
        total_price_per_item = (discounted_price + shipping + tax_amount) * item.quantity

        # Add to totals
        total_price += discounted_price * item.quantity
        total_shipping += shipping * item.quantity
        total_tax += tax_amount * item.quantity
        total_discount += (base_price - discounted_price) * item.quantity

        # Set the total price per item for display in the template
        item.total_price = total_price_per_item

    # Grand total including shipping, tax, and discounts
    grand_total = total_price + total_shipping + total_tax - total_discount

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_shipping': total_shipping,
        'total_tax': total_tax,
        'total_discount': total_discount,
        'grand_total': grand_total,
    })


from django.shortcuts import redirect, get_object_or_404
from .models import Cart, CartItem

@login_required
def remove_from_cart(request, item_id):
    """Remove a specific item from the user's cart."""
    # Fetch the CartItem by the item ID and ensure it belongs to the current user
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    
    item.delete()  # Remove the item from the cart
    return redirect('view_cart')  # Redirect back to the cart view


@login_required
def update_cart_quantity(request, item_id):
    """Update the quantity of a specific item in the user's cart."""
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart_item.quantity = quantity
        cart_item.save()

    return redirect('view_cart')

from django.shortcuts import render, get_object_or_404
from .models import Order





@login_required
def order_confirmation(request, order_id):
    # Get the specific order based on the order_id
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Render the order confirmation page
    return render(request, 'store/order_confirmation.html', {'order': order})


import logging
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import CartItem, UserProfile
from .forms import ShippingForm

logger = logging.getLogger(__name__)

@login_required
def checkout(request):
    logger.info(f"Checkout process started for user: {request.user.email}")
    
    # Fetch cart items
    cart_items = CartItem.objects.filter(user=request.user)
    
    if not cart_items.exists():
        logger.warning(f"User {request.user.email} attempted checkout with empty cart")
        messages.error(request, 'Your cart is empty!')
        return redirect('view_cart')
    
    # Fetch or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        shipping_form = ShippingForm(request.POST, instance=profile)
        if shipping_form.is_valid():
            shipping_form.save()
            logger.info(f"Shipping information updated for user: {request.user.email}")
            messages.success(request, 'Shipping information updated successfully.')
        else:
            logger.warning(f"Invalid shipping form submitted by user: {request.user.email}")
            messages.error(request, 'Please correct the errors in the shipping form.')
            return render(request, 'store/checkout.html', {'shipping_form': shipping_form})
    else:
        shipping_form = ShippingForm(instance=profile)

    # Calculate total price including tax and shipping
    total_amount = Decimal('0.00')
    for item in cart_items:
        product = item.product
        item_price = product.final_price_with_tax_and_shipping() * item.quantity
        total_amount += item_price

    logger.info(f"Total order amount calculated: {total_amount}")

    # Store the total amount in the session (in paise)
    request.session['razorpay_amount'] = int(total_amount * 100)

    # Prepare context for template
    context = {
        'shipping_form': shipping_form,
        'cart_items': cart_items,
        'profile': profile,
        'amount_in_rupees': total_amount,
        'proceed_to_payment_url': reverse('initiate_payment'),
    }
    
    logger.info(f"Checkout page rendered for user: {request.user.email}")
    return render(request, 'store/checkout.html', context)


import logging
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings
import razorpay

logger = logging.getLogger(__name__)
import logging
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings
import razorpay
from .models import UserProfile
from .forms import ShippingForm

logger = logging.getLogger(__name__)

import logging
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings
import razorpay
from .models import UserProfile
from .forms import ShippingForm

logger = logging.getLogger(__name__)
import logging
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings
import razorpay
from .models import UserProfile, CartItem
from .forms import ShippingForm

logger = logging.getLogger(__name__)

@login_required
def initiate_payment(request):
    logger.info(f"Payment initiation started for user: {request.user.email}")

    # Retrieve the total amount from the session
    total_amount = request.session.get('razorpay_amount')
    
    if not total_amount:
        logger.error(f"Total amount not found in session for user: {request.user.email}")
        messages.error(request, 'Unable to retrieve order total. Please try again.')
        return redirect('checkout')

    # Convert from paise to rupees for display
    amount_in_rupees = Decimal(total_amount) / 100

    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Check if shipping address is available
    has_shipping_address = bool(user_profile.address_line_1 and user_profile.city and user_profile.state and user_profile.postal_code)

    # Initialize shipping form if address is not available
    shipping_form = None
    if not has_shipping_address:
        if request.method == 'POST':
            shipping_form = ShippingForm(request.POST, instance=user_profile)
            if shipping_form.is_valid():
                shipping_form.save()
                has_shipping_address = True
                messages.success(request, 'Shipping information updated successfully.')
                # Set a flag in the session to indicate shipping info has been saved
                request.session['shipping_info_saved'] = True
                # Redirect to the same page to show the payment button
                return redirect('initiate_payment')
            else:
                messages.error(request, 'Please correct the errors in the shipping form.')
        else:
            shipping_form = ShippingForm(instance=user_profile)

    # Check if shipping info was just saved
    shipping_info_just_saved = request.session.pop('shipping_info_saved', False)

    # Only proceed with Razorpay order creation if shipping address is available
    razorpay_order = None
    if has_shipping_address:
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            logger.info("Razorpay client initialized successfully")

            razorpay_order = client.order.create({
                'amount': total_amount,
                'currency': settings.RAZORPAY_CURRENCY,
                'payment_capture': '1'
            })
            logger.info(f"Razorpay order created: {razorpay_order['id']} for user: {request.user.email}")
        except razorpay.errors.BadRequestError as e:
            logger.error(f"Razorpay BadRequestError for user {request.user.email}: {str(e)}")
            error_detail = e.error.get('description') if hasattr(e, 'error') and isinstance(e.error, dict) else str(e)
            messages.error(request, f"Error in payment initialization: {error_detail}")
            return redirect('checkout')
        except Exception as e:
            logger.error(f"Unexpected error in payment initiation for user {request.user.email}: {str(e)}", exc_info=True)
            messages.error(request, "An unexpected error occurred. Please try again later.")
            return redirect('checkout')

    # Prepare context for the payment template
    context = {
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'amount': total_amount,
        'amount_in_rupees': amount_in_rupees,
        'currency': settings.RAZORPAY_CURRENCY,
        'callback_url': request.build_absolute_uri(reverse('payment_success')),
        'user_name': request.user.email,  # Using email as name since there's no name field in User model
        'user_email': request.user.email,
        'user_contact': user_profile.phone_number if user_profile.phone_number else '',
        'has_shipping_address': has_shipping_address,
        'shipping_form': shipping_form,
        'shipping_info_just_saved': shipping_info_just_saved,
    }

    if razorpay_order:
        context['razorpay_order_id'] = razorpay_order['id']

    return render(request, 'store/payment.html', context)
import logging
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.conf import settings
import razorpay
from .models import Order, OrderItem, CartItem, UserProfile

logger = logging.getLogger(__name__)

@csrf_exempt
def payment_success(request):
    logger.info("Payment success view called")
    logger.info(f"Request method: {request.method}")
    logger.info(f"POST data: {request.POST}")

    if request.method == "POST":
        try:
            # Initialize Razorpay client
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            logger.info("Razorpay client initialized")

            # Get the Razorpay payment details
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')

            logger.info(f"Payment details: Payment ID: {payment_id}, Order ID: {razorpay_order_id}")

            # Verify the payment signature
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            try:
                client.utility.verify_payment_signature(params_dict)
                logger.info("Payment signature verified successfully")
            except razorpay.errors.SignatureVerificationError as e:
                logger.error(f"Payment signature verification failed: {str(e)}")
                messages.error(request, 'Payment verification failed.')
                return redirect('checkout')

            # Retrieve the order amount from the session
            razorpay_amount = request.session.get('razorpay_amount')
            logger.info(f"Razorpay amount from session: {razorpay_amount}")

            if not razorpay_amount:
                logger.error("Razorpay amount not found in session")
                messages.error(request, 'Order amount not found. Please try again.')
                return redirect('checkout')

            # Check payment status instead of capturing
            payment = client.payment.fetch(payment_id)
            if payment['status'] != 'captured':
                logger.error(f"Payment not captured. Status: {payment['status']}")
                messages.error(request, 'Payment was not successful. Please try again.')
                return redirect('checkout')

            logger.info(f"Payment status: {payment['status']}")

            # Create order and move items from cart to order
            try:
                with transaction.atomic():
                    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
                    logger.info(f"User profile retrieved: {user_profile.id}")

                    order = Order.objects.create(
                        user=request.user,
                        total_price=razorpay_amount / 100,
                        shipping_address=f"{user_profile.address_line_1}, {user_profile.city}, {user_profile.state} - {user_profile.postal_code}",
                        phone_number=user_profile.phone_number,
                        is_paid=True,
                        razorpay_order_id=razorpay_order_id,
                        razorpay_payment_id=payment_id
                    )
                    logger.info(f"Order created: {order.id}")

                    cart_items = CartItem.objects.filter(user=request.user)
                    logger.info(f"Number of cart items: {cart_items.count()}")

                    for cart_item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=cart_item.product,
                            quantity=cart_item.quantity,
                            price=cart_item.product.price
                        )
                        logger.info(f"Order item created: {cart_item.product.name}, Quantity: {cart_item.quantity}")

                    cart_items.delete()
                    logger.info("Cart cleared after order creation")

                messages.success(request, 'Your order has been placed successfully!')
                logger.info(f"Redirecting to order detail page for order: {order.id}")
                return redirect('order_detail', order_id=order.id)

            except Exception as e:
                logger.error(f"Error creating order in database: {str(e)}", exc_info=True)
                messages.error(request, 'Error creating your order. Please contact support.')
                return redirect('checkout')

        except Exception as e:
            logger.error(f"Unexpected error in payment_success: {str(e)}", exc_info=True)
            messages.error(request, 'An unexpected error occurred. Please contact support.')

    logger.warning("Payment success view called with non-POST method")
    return redirect('checkout')


import logging
from django.shortcuts import render
from django.contrib import messages
from .models import Order

logger = logging.getLogger(__name__)

def order_detail(request):
    user = request.user
    logger.info(f"Fetching orders for user: {user.email} (ID: {user.id})")
    
    orders = Order.objects.filter(user=user).order_by('-created_at')
    logger.info(f"Number of orders found for user {user.email}: {orders.count()}")
    
    for order in orders:
        logger.info(f"Order ID: {order.id}, User: {order.user.email}, Total Amount: {order.total_price}, Created At: {order.created_at}")
        
    if not orders:
        logger.warning(f"No orders found for user: {user.email}")
        messages.warning(request, "You haven't placed any orders yet.")
    
    context = {
        'orders': orders,
        'user_email': user.email,
        'total_orders': orders.count(),
    }
    
    return render(request, 'store/order_list.html', context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Order

@login_required
def user_orders_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    
    context = {
        'orders': orders
    }
    return render(request, 'store/order_list.html', context)

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_detail.html', {'order': order})




from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Order, OrderItem, Product

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .models import Product, OrderItem, Order

@login_required
@user_passes_test(lambda u: u.is_seller)
def seller_orders(request):
    # Get all products created by this seller
    seller_products = Product.objects.filter(created_by=request.user)
    
    # Get all order items that contain the seller's products
    order_items = OrderItem.objects.filter(product__in=seller_products).select_related('order')
    
    # Get unique orders
    orders = Order.objects.filter(items__in=order_items).distinct().order_by('-created_at')
    
    # Get total orders count
    total_orders = orders.count()
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    
    context = {
        'orders': orders,
        'total_orders': total_orders
    }
    return render(request, 'store/seller_orders.html', context)


@login_required
@user_passes_test(lambda u: u.is_seller)
def seller_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    seller_products = Product.objects.filter(created_by=request.user)
    order_items = order.items.filter(product__in=seller_products)
    
    total_seller_amount = sum(item.quantity * item.price for item in order_items)
    
    context = {
        'order': order,
        'order_items': order_items,
        'total_seller_amount': total_seller_amount,
    }
    return render(request, 'store/seller_order_detail.html', context)

@login_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, items__product__created_by=request.user)
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
    return redirect('seller_orders')

@login_required
@user_passes_test(lambda u: u.is_seller)
def printable_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, items__product__created_by=request.user)
    order_items = order.items.filter(product__created_by=request.user)
    total_seller_amount = sum(item.price * item.quantity for item in order_items)

    context = {
        'order': order,
        'order_items': order_items,
        'total_seller_amount': total_seller_amount,
    }
    return render(request, 'store/printable_order_detail.html', context)
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, F
from django.contrib import messages
from django.urls import reverse
from decimal import Decimal

from .models import Product, Order, OrderItem, SettlementRequest

@user_passes_test(lambda u: u.is_seller)
def seller_payments(request):
    # Get all products created by this seller
    seller_products = Product.objects.filter(created_by=request.user)

    # Get all order items that contain the seller's products
    order_items = OrderItem.objects.filter(product__in=seller_products, order__is_paid=True)

    # Calculate total sales, commission, tax, shipping, and net earnings
    total_sales = order_items.aggregate(
        total=Sum(F('product__price') * F('quantity') * (1 + F('product__tax_percentage') / 100) + F('product__shipping_charge'))
    )['total'] or Decimal('0.00')

    total_tax = order_items.aggregate(
        total=Sum(F('product__price') * F('quantity') * F('product__tax_percentage') / 100)
    )['total'] or Decimal('0.00')

    total_shipping = order_items.aggregate(
        total=Sum(F('product__shipping_charge') * F('quantity'))
    )['total'] or Decimal('0.00')

    total_commission = order_items.aggregate(
        total=Sum(F('product__price') * F('quantity') * F('product__category__commission') / 100)
    )['total'] or Decimal('0.00')

    total_net_earnings = total_sales - total_commission

    # Get unique orders for detailed view
    orders = Order.objects.filter(items__in=order_items).distinct().order_by('-created_at')

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(orders, 10)
    try:
        paginated_orders = paginator.page(page)
    except PageNotAnInteger:
        paginated_orders = paginator.page(1)
    except EmptyPage:
        paginated_orders = paginator.page(paginator.num_pages)

    # Refresh the settlement request status for each order
    for order in paginated_orders:
        order.refresh_from_db()
        order_items = order.items.filter(product__created_by=request.user)
        order.total_product_price = sum(item.product.price * item.quantity for item in order_items)
        order.total_tax = sum(item.product.price * (item.product.tax_percentage / 100) * item.quantity for item in order_items)
        order.total_shipping = sum(item.product.shipping_charge * item.quantity for item in order_items)
        order.total_commission = sum(item.product.price * (item.product.category.commission / 100) * item.quantity for item in order_items)
        order.net_earnings = order.total_product_price + order.total_tax + order.total_shipping - order.total_commission

    if request.method == 'POST' and 'request_settlement' in request.POST:
        selected_order_ids = request.POST.getlist('selected_orders')
        if selected_order_ids:
            url = reverse('settlement_requests')
            url += f'?selected_order_ids={",".join(selected_order_ids)}'
            return redirect(url)
        else:
            messages.warning(request, 'Please select at least one order for settlement.')
            return redirect('seller_payments')

    context = {
        'total_sales': total_sales,
        'total_tax': total_tax,
        'total_shipping': total_shipping,
        'total_commission': total_commission,
        'net_earnings': total_net_earnings,
        'orders': paginated_orders,
    }
    return render(request, 'store/seller_payments.html', context)
@login_required
@user_passes_test(lambda u: u.is_seller)
def settlement_requests(request):
    selected_order_ids = request.GET.get('selected_order_ids', '')
    
    if request.method == 'POST':
        if selected_order_ids:
            selected_order_ids_list = [int(order_id) for order_id in selected_order_ids.split(',')]
            orders = Order.objects.filter(id__in=selected_order_ids_list, items__product__created_by=request.user).distinct()

            total_order_sales = Decimal('0.00')
            total_order_commission = Decimal('0.00')
            total_order_net_earnings = Decimal('0.00')

            for order in orders:
                order_items = order.items.filter(product__created_by=request.user)
                order_total = sum(item.product.price * item.quantity for item in order_items)
                order_commission = sum(item.product.price * item.quantity * (item.product.category.commission / 100) for item in order_items)
                
                total_order_sales += order_total
                total_order_commission += order_commission
                total_order_net_earnings += order_total - order_commission

                order.settlement_request_status = 'requested'
                order.save()

            settlement_request = SettlementRequest.objects.create(
                seller=request.user,
                total_sales=total_order_sales,
                total_commission=total_order_commission,
                net_earnings=total_order_net_earnings
            )
            messages.success(request, 'Settlement request submitted successfully.')
            return redirect('seller_payments')

    settlement_requests = SettlementRequest.objects.filter(seller=request.user)
    selected_orders = []
    total_selected_sales = Decimal('0.00')
    total_selected_commission = Decimal('0.00')
    total_selected_net_earnings = Decimal('0.00')

    if selected_order_ids:
        selected_order_ids_list = [int(order_id) for order_id in selected_order_ids.split(',')]
        selected_orders = Order.objects.filter(id__in=selected_order_ids_list, items__product__created_by=request.user).distinct()

        for order in selected_orders:
            order_items = order.items.filter(product__created_by=request.user)
            order_total = sum(item.product.price * item.quantity for item in order_items)
            order_commission = sum(item.product.price * item.quantity * (item.product.category.commission / 100) for item in order_items)
            
            total_selected_sales += order_total
            total_selected_commission += order_commission
            total_selected_net_earnings += order_total - order_commission

    context = {
        'settlement_requests': settlement_requests,
        'selected_orders': selected_orders,
        'selected_order_ids': selected_order_ids,
        'total_selected_sales': total_selected_sales,
        'total_selected_commission': total_selected_commission,
        'total_selected_net_earnings': total_selected_net_earnings,
    }
    return render(request, 'store/settlement_requests.html', context)