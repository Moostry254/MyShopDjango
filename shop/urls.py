# shop/urls.py

from django.urls import path
from . import views

app_name = 'shop' # Defines the application namespace

urlpatterns = [
    # Specific paths should come before more general paths

    # Cart Pages/Actions
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update-quantity/<int:product_id>/', views.cart_update_quantity, name='cart_update_quantity'),

    # Checkout Page
    path('checkout/', views.checkout_view, name='checkout_view'),

    # Order History Page
    path('orders/', views.order_history, name='order_history'),

    # Wishlist Pages
    path('wishlist/', views.wishlist_view, name='wishlist_view'),
    path('wishlist/add/<int:product_id>/', views.wishlist_add, name='wishlist_add'),
    path('wishlist/remove/<int:product_id>/', views.wishlist_remove, name='wishlist_remove'),

    # Homepage - lists all products
    path('', views.product_list, name='product_list'),
    # Product list filtered by category (this is the general pattern)
    path('<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    # Product detail page (this also uses slugs, but with an int ID, so it's more specific than category_slug alone)
    path('<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
]
