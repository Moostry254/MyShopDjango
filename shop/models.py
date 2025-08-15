# shop/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

# Custom User Model (Recommended for future flexibility)
class CustomUser(AbstractUser):
    # Add any additional fields you might want for your users here
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username

# Product Category Model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True, help_text="A short label for URLs, containing only letters, numbers, underscores or hyphens.") # For clean URLs

    class Meta:
        verbose_name_plural = "Categories" # Correct plural name for admin interface

    def __str__(self):
        return self.name

# Product Model
class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/%Y/%m/%d/', blank=True, null=True) # Images will go into media/products/year/month/day/
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True, help_text="A short label for URLs, containing only letters, numbers, underscores or hyphens.") # For clean URLs

    class Meta:
        ordering = ('name',) # Order products by name by default
        indexes = [
            models.Index(fields=['id', 'slug']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # This method is used by Django to figure out the URL for a specific product instance
        from django.urls import reverse
        return reverse('shop:product_detail', args=[self.id, self.slug])

# Slideshow Slide Model
class Slide(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='slides/%Y/%m/%d/') # Images for slides
    link_url = models.URLField(max_length=500, blank=True, null=True, help_text="Optional URL for the slide's call-to-action button.")
    order = models.PositiveIntegerField(default=0, help_text="Order in which slides appear (lower number first).")
    is_active = models.BooleanField(default=True, help_text="Whether this slide should be displayed in the slideshow.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at'] # Order by custom 'order', then by creation time
        verbose_name = "Slide"
        verbose_name_plural = "Slides"

    def __str__(self):
        return self.title

# Order Model
class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    # Using null=True, blank=True for user in case of guest checkout or anonymous orders
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    # Status field for tracking (e.g., Pending, Processing, Shipped, Delivered, Cancelled)
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    class Meta:
        ordering = ('-created',) # Order by most recent orders

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        # Calculate total cost by summing up cost of all order items
        return sum(item.get_cost() for item in self.items.all())

# Order Item Model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Price at the time of purchase
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        # Calculate cost for a single order item
        return self.price * self.quantity

# Wishlist Model
class Wishlist(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist for {self.user.username}"

# Wishlist Item Model
class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wishlist', 'product') # A product can only be in a wishlist once
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user.username}'s wishlist"

# NEW: Cart Model
class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    # You could also consider a session_key for anonymous users if you plan to implement that.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username if self.user else 'Anonymous'}"

    def get_total_price(self):
        # Calculate total price of all items in the cart
        return sum(item.get_cost() for item in self.items.all())

# NEW: Cart Item Model
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Price at the time item was added
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product') # A product can only be added once per cart (quantity is handled)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"

    def get_cost(self):
        return self.price * self.quantity
