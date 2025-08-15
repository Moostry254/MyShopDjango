# shop/admin.py

from django.contrib import admin
from .models import Category, Product, CustomUser, Slide, Order, OrderItem, Wishlist, WishlistItem, Cart, CartItem # <-- IMPORT NEW MODELS
from django.contrib.auth.admin import UserAdmin

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'price', 'stock', 'available', 'created', 'updated']
    list_filter = ['available', 'created', 'updated', 'category']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (('Contact Info', {'fields': ('phone_number', 'address')}),)
    )
    list_display = UserAdmin.list_display + ('phone_number', 'address',)

@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'description']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'email', 'address', 'paid', 'status', 'created', 'updated']
    list_filter = ['paid', 'status', 'created', 'updated']
    search_fields = ['id', 'first_name', 'last_name', 'email']
    inlines = [OrderItemInline]
    list_editable = ['status', 'paid']

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
    search_fields = ['user__username']

@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['wishlist', 'product', 'added_at']
    list_filter = ['added_at']
    search_fields = ['wishlist__user__username', 'product__name']

# NEW: Inline for CartItem to be displayed within CartAdmin
class CartItemInline(admin.TabularInline):
    model = CartItem
    raw_id_fields = ['product'] # Improves performance for many products
    extra = 1 # Show one empty form for adding new items

# NEW: Register Cart model
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'updated_at', 'get_total_price_display']
    search_fields = ['user__username']
    inlines = [CartItemInline]
    readonly_fields = ['created_at', 'updated_at']

    # Custom method to display total price in list view
    def get_total_price_display(self, obj):
        return f"&#x09F3;{obj.get_total_price():.2f}"
    get_total_price_display.short_description = 'Total Price'
    get_total_price_display.admin_order_field = 'id' # Allow sorting by ID

