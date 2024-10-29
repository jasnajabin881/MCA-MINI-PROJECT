from django.urls import path
from . import views

urlpatterns = [
    # Registration and login
    path("register/", views.register_user, name="register_user"),
    path("register-seller/", views.register_seller, name="register_seller"),
    path("login/", views.user_login, name="user_login"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("", views.home, name="home"),  # Default home URL
    path("admin-login/", views.admin_login, name="admin_login"),
    path("admin-logout/", views.admin_logout, name="admin_logout"),
    path("seller-dashboard/", views.seller_dashboard, name="seller_dashboard"),
    path("logout/", views.user_logout, name="user_logout"),
    # Admin and Seller product management
    path("admin-dashboard/sellers/", views.list_sellers, name="admin_sellers"),
    path(
        "admin-dashboard/sellers/delete/<int:seller_id>/",
        views.delete_seller,
        name="delete_seller",
    ),
    path(
        "admin-dashboard/sellers/approve/<int:seller_id>/",
        views.approve_seller,
        name="approve_seller",
    ),
    path("admin-dashboard/categories/", views.category_list, name="category_list"),
    path("admin-dashboard/categories/add/", views.add_category, name="add_category"),
    path(
        "admin-dashboard/categories/edit/<int:category_id>/",
        views.edit_category,
        name="edit_category",
    ),
    path(
        "admin-dashboard/categories/delete/<int:category_id>/",
        views.delete_category,
        name="delete_category",
    ),

    path('settlement-requests_admin/', views.settlement_requests_list_admin, name='settlement_requests_list_admin'),
        path('settlement-request/<int:request_id>/', views.settlement_request_detail, name='settlement_request_detail'),

    path('update-settlement-request/<int:request_id>/', views.update_settlement_request_admin, name='update_settlement_request_admin'),
    path("products/", views.list_products, name="list_products"),
    path("products/add/", views.add_product, name="add_product"),
    path("products/edit/<int:product_id>/", views.edit_product, name="edit_product"),
    # User product-related URLs
    path(
        "shop/", views.product_list, name="product_list"
    ),  # View all products for users
    path(
        "shop/<int:product_id>/", views.product_detail, name="product_detail"
    ),  # View product details
    path(
        "category/<int:category_id>/",
        views.list_products_by_category,
        name="list_products_by_category",
    ),
    # Cart-related URLs for users
    path(
        "cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"
    ),  # Add product to cart
    path("cart/", views.view_cart, name="view_cart"),  # View cart
    path(
        "cart/update/<int:item_id>/",
        views.update_cart_quantity,
        name="update_cart_quantity",
    ),
    path(
        "cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"
    ),  # Remove product from cart
    # Checkout-related URLs for users
    path("checkout/", views.checkout, name="checkout"),  # Proceed to checkout
    path(
        "order-confirmation/<int:order_id>/",
        views.order_confirmation,
        name="order_confirmation",
    ),  # Order confirmation page
    path(
        "payment-success/", views.payment_success, name="payment_success"
    ),  # Add this line
    path("orders/", views.user_orders_list, name="user_orders_list"),
    path(
        "order-confirmation/<int:order_id>/",
        views.order_confirmation,
        name="order_confirmation",
    ),
    path("initiate-payment/", views.initiate_payment, name="initiate_payment"),
    
    
    
    
    path("order/<int:order_id>/", views.order_detail, name="order_detail"),
    path('seller/orders/', views.seller_orders, name='seller_orders'),
    path('seller/orders/<int:order_id>/', views.seller_order_detail, name='seller_order_detail'),
    path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('seller/order/<int:order_id>/print/', views.printable_order_detail, name='printable_order_detail'),
   
    path('seller/payments/', views.seller_payments, name='seller_payments'),
    path('settlement-requests/', views.settlement_requests, name='settlement_requests'),
    path('settlement-requests/select/', views.settlement_requests, name='settlement_requests_with_orders'),
 

]
