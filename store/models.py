from django.db import models
from django.conf import settings
# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from .models import *
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        
        # If the user is a seller, they are inactive by default
        if extra_fields.get('is_seller', False):
            extra_fields.setdefault('is_active', False)
        else:
            extra_fields.setdefault('is_active', True)  # Normal users are active by default
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_admin') is not True:
            raise ValueError('Superuser must have is_admin=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_seller = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.email} - Profile"
class SellerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    name = models.CharField(max_length=100)
    business_name = models.CharField(max_length=150)
    tax_info = models.CharField(max_length=100)
    location = models.CharField(max_length=150)
    address = models.TextField()

    def __str__(self):
        return self.business_name
    

class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    commission = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Commission for admin
    status = models.BooleanField(default=True)  # Active or Inactive

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    sku = models.CharField(max_length=100, unique=True)
    thumbnail = models.ImageField(upload_to='products/thumbnails/', blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image1 = models.ImageField(upload_to='products/', blank=True, null=True)
    image2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image3 = models.ImageField(upload_to='products/', blank=True, null=True)
    stock = models.IntegerField()
    discount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    weight = models.CharField(max_length=100, blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True, null=True)
    status = models.BooleanField(default=True)
    shipping_charge = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    tax_percentage = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)  # e.g. 5% tax
    offer = models.CharField(max_length=255, blank=True, null=True)  # Offers description
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    related_products = models.ManyToManyField('self', blank=True)  # Related products

    def __str__(self):
        return self.name

    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return sum(review.rating for review in reviews) / reviews.count()
        return 0

    def total_reviews(self):
        return self.reviews.count()

    def discount_price(self):
        if self.discount:
            return self.price - (self.price * (self.discount / 100))
        return self.price

    def final_price_with_tax_and_shipping(self):
        price_after_discount = self.discount_price()
        tax_amount = price_after_discount * (self.tax_percentage / 100)
        return price_after_discount + tax_amount + self.shipping_charge

    def is_in_stock(self):
        return self.stock > 0



from django.db import models
from django.conf import settings
class SettlementRequest(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='settlement_requests')
    total_sales = models.DecimalField(max_digits=10, decimal_places=2)
    total_commission = models.DecimalField(max_digits=10, decimal_places=2)
    net_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    admin_comment = models.TextField(blank=True, null=True)
class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),)
    settlement_request = models.ForeignKey(SettlementRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    settlement_request_status = models.CharField(max_length=20, default='not_requested', choices=[
        ('not_requested', 'Not Requested'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ])

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sold_orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    phone_number = models.CharField(max_length=15)
    is_paid = models.BooleanField(default=False)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.email}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Add this line

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)  # To ensure that only users who bought the product can review
    rating = models.PositiveIntegerField(default=1)  # Rating out of 5
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')  # User can leave only one review per product
        constraints = [
            models.CheckConstraint(
                check=models.Q(order_item__isnull=False),
                name='review_only_for_purchased_products'
            )
        ]

    def __str__(self):
        return f'{self.rating} stars by {self.user} on {self.product.name}'
class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user.email}"

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Ensure it's related to the user
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.quantity * self.product.price

    def __str__(self):
        return f'{self.product.name} (x{self.quantity})'
    


from django.db import models
from django.conf import settings

