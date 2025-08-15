# shop/views.py

from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, Slide, Order, OrderItem, Wishlist, WishlistItem, Cart, CartItem, \
    CustomUser  # Import all models
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction  # For atomic order creation
from django.contrib import messages  # For displaying messages to the user


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    slides = Slide.objects.filter(is_active=True).order_by('order')

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    return render(request, 'shop/product_list.html', {
        'category': category,
        'categories': categories,
        'products': products,
        'slides': slides,
    })


def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    return render(request, 'shop/product_detail.html', {'product': product})


# Order History View (Requires user to be logged in)
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created')
    return render(request, 'shop/order_history.html', {'orders': orders})


# Wishlist View (Requires user to be logged in)
@login_required
def wishlist_view(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'shop/wishlist.html', {'wishlist': wishlist})


# Add to Wishlist (requires POST request and user login)
@login_required
@require_POST
def wishlist_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist_item, item_created = WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
    if item_created:
        messages.success(request, f'"{product.name}" added to your wishlist.')
        return JsonResponse(
            {'status': 'success', 'message': 'Product added to wishlist.', 'product_name': product.name})
    else:
        messages.info(request, f'"{product.name}" is already in your wishlist.')
        return JsonResponse(
            {'status': 'info', 'message': 'Product is already in your wishlist.', 'product_name': product.name})


# Remove from Wishlist (requires POST request and user login)
@login_required
@require_POST
def wishlist_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    deleted_count, _ = WishlistItem.objects.filter(wishlist=wishlist, product=product).delete()
    if deleted_count > 0:
        messages.success(request, f'"{product.name}" removed from your wishlist.')
        return JsonResponse(
            {'status': 'success', 'message': 'Product removed from wishlist.', 'product_name': product.name})
    else:
        messages.info(request, f'"{product.name}" was not found in your wishlist.')
        return JsonResponse(
            {'status': 'info', 'message': 'Product was not found in your wishlist.', 'product_name': product.name})


# CART FUNCTIONALITY
@login_required
def cart_view(request):
    # Get or create the user's cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'shop/cart.html', {'cart': cart})


@login_required
@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))  # Get quantity from POST, default to 1

    if quantity <= 0:
        messages.error(request, 'Quantity must be at least 1.')
        return JsonResponse({'status': 'error', 'message': 'Quantity must be at least 1.'})

    if product.stock < quantity:
        messages.error(request, f'Not enough stock for "{product.name}". Available: {product.stock}')
        return JsonResponse({'status': 'error', 'message': 'Not enough stock.'})

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity, 'price': product.price}  # Set initial quantity and price if new item
    )

    if not item_created:
        # If item already exists in cart, update quantity
        old_quantity = cart_item.quantity
        new_total_quantity = old_quantity + quantity
        if product.stock < new_total_quantity:
            messages.error(request,
                           f'Cannot add more "{product.name}". Only {product.stock - old_quantity} more available.')
            return JsonResponse({'status': 'error', 'message': 'Cannot add more. Not enough stock.'})
        cart_item.quantity = new_total_quantity
        cart_item.save()
        messages.success(request, f'{quantity} more of "{product.name}" added to cart. Total: {cart_item.quantity}.')
    else:
        messages.success(request, f'"{product.name}" added to cart.')

    return JsonResponse({'status': 'success', 'message': 'Product added to cart.'})


@login_required
@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)

    cart_item.delete()
    messages.success(request, f'"{product.name}" removed from cart.')
    return JsonResponse({'status': 'success', 'message': 'Product removed from cart.'})


@login_required
@require_POST
def cart_update_quantity(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    new_quantity = int(request.POST.get('quantity', 1))  # New desired quantity

    if new_quantity <= 0:
        cart_remove(request, product_id)  # If quantity is 0 or less, remove item
        return JsonResponse({'status': 'removed', 'message': f'"{product.name}" removed from cart.'})

    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)

    if product.stock < new_quantity:
        messages.error(request, f'Not enough stock for "{product.name}". Max available: {product.stock}')
        return JsonResponse({'status': 'error', 'message': f'Not enough stock. Max: {product.stock}'})

    cart_item.quantity = new_quantity
    cart_item.save()
    messages.success(request, f'Quantity for "{product.name}" updated to {new_quantity}.')
    return JsonResponse({'status': 'success', 'message': 'Quantity updated.', 'new_quantity': new_quantity,
                         'new_item_cost': cart_item.get_cost()})


# CHECKOUT FUNCTIONALITY
@login_required
def checkout_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    if not cart.items.exists():
        messages.warning(request, "Your cart is empty. Please add items before checking out.")
        return redirect('shop:product_list')

    if request.method == 'POST':
        # This is a simplified checkout process. In a real app, you'd use forms.
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        postal_code = request.POST.get('postal_code')
        city = request.POST.get('city')

        if not all([first_name, last_name, email, address, postal_code, city]):
            messages.error(request, "Please fill in all required shipping details.")
            return render(request, 'shop/checkout.html', {'cart': cart})

        try:
            with transaction.atomic():  # Ensure atomicity: either all or none of the operations succeed
                # Create the Order
                order = Order.objects.create(
                    user=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    address=address,
                    postal_code=postal_code,
                    city=city,
                    # paid=False by default
                    status='Pending'
                )

                # Move items from cart to OrderItems and update product stock
                for cart_item in cart.items.all():
                    if cart_item.product.stock < cart_item.quantity:
                        raise ValueError(
                            f"Not enough stock for {cart_item.product.name}. Only {cart_item.product.stock} available.")

                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        price=cart_item.price,  # Price at the time of order
                        quantity=cart_item.quantity
                    )
                    # Decrease product stock
                    cart_item.product.stock -= cart_item.quantity
                    cart_item.product.save()

                # Clear the cart after successful order creation
                cart.items.all().delete()

                messages.success(request, f"Your order #{order.id} has been placed successfully!")
                return redirect('shop:order_history')  # Redirect to order history page
        except ValueError as e:
            messages.error(request, f"Order failed: {e}")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}. Please try again.")

    return render(request, 'shop/checkout.html', {'cart': cart})

# --- TEMPORARY: FOR ONE-TIME ADMIN CREATION ONLY ---
def create_initial_superuser(request):
    """
    A temporary view to create an initial superuser on Render.
    This view MUST be removed immediately after use for security.
    """
    if request.method == 'GET':
        username = os.environ.get('DJANGO_ADMIN_USERNAME', 'renderadmin') # Get from environment or use default
        password = os.environ.get('DJANGO_ADMIN_PASSWORD', 'renderpassword') # Get from environment or use default

        # Only create if the user doesn't exist to prevent errors on repeated access
        if not User.objects.filter(username=username).exists():
            try:
                user = User.objects.create_superuser(username=username, email='admin@myshop.com', password=password)
                user.save()
                return HttpResponse(f"Superuser '{username}' created successfully. Now go to /admin/ and login. REMOVE THIS VIEW IMMEDIATELY!", status=200)
            except Exception as e:
                return HttpResponse(f"Error creating superuser: {e}. REMOVE THIS VIEW AFTER DEBUGGING!", status=500)
        else:
            return HttpResponse(f"Superuser '{username}' already exists. REMOVE THIS VIEW IMMEDIATELY!", status=200)
    return HttpResponse("Access this view via GET request to create superuser. REMOVE THIS VIEW!", status=405)

# --- END TEMPORARY CODE ---