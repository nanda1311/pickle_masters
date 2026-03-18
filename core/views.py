from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Cart
from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.models import User
from django.contrib import messages as toast
from .models import Product, ProductImage, Category, Order, Address
from django.shortcuts import render, get_object_or_404,redirect
from .forms import *
from django.http import JsonResponse
from django.contrib.auth import authenticate, login ,logout 
from django.contrib import messages
from django.http import JsonResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from django.db.models import Q


# frontend

def home(request):
    # Get 'Veg' products
    veg_products = Product.objects.filter(
        category__name='Veg',
        status='active',
        in_stock='in_stock'
    ).order_by('-created_at')[:10]

    # Get 'Non Veg' products
    non_veg_products = Product.objects.filter(
        category__name='Non Veg',
        status='active',
        in_stock='in_stock'
    ).order_by('-created_at')[:10]

    # Get 'Gongura Combination' products (NEW)
    gongura_products = Product.objects.filter(
        category__name='Gongura  Combination', # Assuming the category name is exactly this
        status='active',
        in_stock='in_stock'
    ).order_by('-created_at')[:10]

    # Prepare product data with sizes
    def format_products_with_sizes(products):
        product_list = []
        for product in products:
            size_data = []
            # Prefetching sizes would be more efficient, but keeping your original loop structure
            for size in product.sizes.all(): 
                size_data.append({
                    'size': size.size,
                    'price': float(size.price),
                    'discounted_price': float(size.discounted_price) if size.discounted_price else None,
                })
            product_list.append({
                'id': product.id,
                'name': product.name,
                'image': product.image.url if product.image else '',
                'category': product.category.name if product.category else '',
                'in_stock': product.in_stock,
                'slug':product.slug,
                'stock_count': getattr(product, 'stock_count', 0),
                'sizes': size_data,
            })
        return product_list

    context = {
        'veg_products': format_products_with_sizes(veg_products),
        'non_veg_products': format_products_with_sizes(non_veg_products),
        'gongura_products': format_products_with_sizes(gongura_products), # NEW
        'total_veg_products': veg_products.count(),
        'total_non_veg_products': non_veg_products.count(),
        'total_gongura_products': gongura_products.count(), # NEW
    }

    return render(request, 'frontend/home.html', context)

def category_list_view(request):
    # This reads the category parameter passed by the "View More" link
    category_name = request.GET.get('category') 
    
    # You might want to map 'veg-pickles' (from the URL) back to 'Veg' (the DB name)
    if category_name == 'veg-pickles':
        db_category_name = 'Veg'
    elif category_name == 'non-veg-pickles':
        db_category_name = 'Non Veg'
    elif category_name == 'gongura-combination':
        db_category_name = 'gongura combination'
    else:
        db_category_name = None

    products = []
    category_object = None
    
    if db_category_name:
        try:
            category_object = Category.objects.get(name=db_category_name)
            products = Product.objects.filter(
                category=category_object, 
                status='active', 
                in_stock='in_stock'
            ).order_by('-created_at')
        except Category.DoesNotExist:
            products = [] # Category not found

    context = {
        'products': products,
        'category_name': category_object.name if category_object else 'All Pickles',
    }
    
    # You will need a template for this view, e.g., 'frontend/category_list.html'
    return render(request, 'frontend/category_list.html', context)
    categories = Category.objects.all()

def cateogry_products(request, slug):
    category = Category.objects.get(slug=slug)

    print(category.name)
    products = Product.objects.filter(category=category)
    veg_products = Product.objects.all()
    non_veg_products = Product.objects.all()
    gongura_products = Product.objects.all()

    # Prepare product data with sizes
    def format_products_with_sizes(products):
        product_list = []
        for product in products:
            size_data = []
            for size in product.sizes.all():
                size_data.append({
                    'size': size.size,
                    'price': float(size.price),
                    'discounted_price': float(size.discounted_price) if size.discounted_price else None,
                })
            product_list.append({
                'id': product.id,
                'name': product.name,
                'image': product.image.url if product.image else '',
                'category': product.category.name if product.category else '',
                'in_stock': product.in_stock,
                'slug':product.slug,
                'stock_count': getattr(product, 'stock_count', 0),
                'sizes': size_data,
            })
        return product_list

    context = {
        'category': category,
        'categories': categories,
        'veg_products': veg_products,
        'non_veg_products': non_veg_products,
        'gongura_products': gongura_products, 

        'products': format_products_with_sizes(products),
    }
    return render(request, 'frontend/category-products.html', context)

def cart_items(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0
    addresses = request.user.addresses.all()

    for product_id, item in cart.items():
        total_price = item['price'] * item['quantity']
        items.append({
            'id': product_id,
            'name': item['name'],
            'price': item['price'],
            'quantity': item['quantity'],
            'total_price': total_price,
            'image_url': item['image_url'],
        })
        total += total_price

    return JsonResponse({'items': items, 'cart_total': total ,'addresses': addresses})

def update_cart_quantity(request, product_id):
    import json
    data = json.loads(request.body)
    action = data.get('action')
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        if action == 'increment':
            cart[str(product_id)]['quantity'] += 1
        elif action == 'decrement' and cart[str(product_id)]['quantity'] > 1:
            cart[str(product_id)]['quantity'] -= 1
        request.session['cart'] = cart
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Product not found in cart'})



@login_required(login_url='login') 
def cart_view(request):
    """Display all cart items of the logged-in user"""
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    cart_total = sum(item.subtotal() for item in cart_items)
    categories = Category.objects.all()
    category = Category.objects.all()
    veg_products = Product.objects.all()
    non_veg_products = Product.objects.all()
    addresses = request.user.addresses.all()


    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'category': category,
        'categories': categories,
        'veg_products': veg_products,
        'non_veg_products': non_veg_products,
        'addresses': addresses

    }
    return render(request, 'frontend/cart.html', context)

@login_required
def delete_cart_item(request, cart_id):
    if request.method == "POST":
        cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
        cart_item.delete()
        return JsonResponse({
            "success": True,
            "message": "Item removed successfully"
        })
    else:
        return JsonResponse({
            "success": False,
            "error": "Invalid request method"
        }, status=400)

@login_required
@csrf_exempt
def update_cart_quantity(request, cart_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            action = data.get("action")

            cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)

            # Adjust quantity
            if action == "increment":
                cart_item.quantity += 1
            elif action == "decrement" and cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                return JsonResponse({"success": False, "error": "Invalid action or quantity"})

            cart_item.save()

            return JsonResponse({
                "success": True,
                "new_quantity": cart_item.quantity,
                "new_subtotal": float(cart_item.subtotal()),
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method"})

@login_required
def get_cart_items(request):
    """
    Return all cart items for the current logged-in user as JSON.
    """
    cart_items = Cart.objects.filter(user=request.user)
    data = []
    cart_total = 0

    for item in cart_items:
        total_price = item.quantity * item.price_at_addition
        cart_total += total_price
        data.append({
            "id": item.id,
            "name": item.product.name,
            "image_url": item.product.image.url if item.product.image else "",
            "quantity": item.quantity,
            "price": float(item.price_at_addition),
            "total_price": float(total_price),
        })

    return JsonResponse({
        "cart_items": data,
        "cart_total": float(cart_total)
    })

def product_detail(request, slug):
    product = Product.objects.get(slug=slug)
    categories = Category.objects.all()
    category = product.category
    products = Product.objects.filter(status='active', category=category).order_by('-created_at')[:4]
    
    veg_products = Product.objects.filter(
        category__name='Veg',
        status='active',
        in_stock='in_stock'
    ).order_by('-created_at')[:10]
    
    non_veg_products = Product.objects.filter(
        category__name='Non Veg',
        status='active',
        in_stock='in_stock'
    ).order_by('-created_at')[:10]

    # Function to format products with sizes, reused from home view
    def format_products_with_sizes(products):
        product_list = []
        for product in products:
            size_data = []
            for size in product.sizes.all():  # Assuming sizes is a related manager
                size_data.append({
                    'size': size.size,
                    'price': float(size.price),
                    'discounted_price': float(size.discounted_price) if size.discounted_price else None,
                })
            product_list.append({
                'id': product.id,
                'name': product.name,
                'image': product.image.url if product.image else '',
                'category': product.category.name if product.category else '',
                'in_stock': product.in_stock,
                'slug': product.slug,
                'stock_count': getattr(product, 'stock_count', 0),
                'sizes': size_data,
            })
        return product_list

    context = {
        'veg_products': veg_products,
        'non_veg_products': non_veg_products,
        'categories': categories,
        'product': product,
        'products': format_products_with_sizes(products),  # Formatted with sizes
        'sizes': product.sizes.all()  # For the main product
    }
    return render(request, 'frontend/product-detail.html', context)

@csrf_exempt
def add_to_cart(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({
                "status": "error",
                "message": "User not authenticated. Please login."
            }, status=401)
        try:
            data = json.loads(request.body)
            product_id = data.get("product_id")
            size = data.get("size")
            preference = data.get("preference")
            quantity = int(data.get("quantity", 1))

            product = Product.objects.get(id=product_id)

            if not size:
                first_size = product.sizes.first()
                if not first_size:
                    return JsonResponse({"success": False, "message": "No size available for this product."})
                size = first_size.size
                price = float(first_size.discounted_price or first_size.price)
            else:
                # Get the selected size’s price
                size_obj = product.sizes.filter(size=size).first()
                if not size_obj:
                    return JsonResponse({"success": False, "message": "Invalid size selected."})
                price = float(size_obj.discounted_price or size_obj.price)


            # ✅ Create or update cart
            cart_item, created = Cart.objects.get_or_create(
                user=request.user,
                product=product,
                size=size,
                preference=preference,
                defaults={"quantity": quantity, "price_at_addition": price}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            return JsonResponse({"success": True, "message": f"{product.name} added to cart."})

        except Product.DoesNotExist:
            return JsonResponse({"success": False, "message": "Product not found."}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request method."}, status=400)

@login_required
@csrf_exempt
def checkout_from_cart(request):

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    address_id = data.get("address_id")
    payment_method = data.get("payment_method")

    if not address_id:
        return JsonResponse({"success": False, "message": "address_id is required"}, status=400)
    if payment_method not in ["cod", "online"]:
        return JsonResponse({"success": False, "message": "Invalid payment_method"}, status=400)

    # Fetch address
    try:
        address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        return JsonResponse({"success": False, "message": "Address not found"}, status=404)

    # Fetch cart items
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    if not cart_items.exists():
        return JsonResponse({"success": False, "message": "Cart is empty"}, status=400)

    # === ONLINE PAYMENT DISABLED ===
    if payment_method == "online":
        return JsonResponse({
            "success": False,
            "message": "Online payment is currently disabled. Please use Cash on Delivery."
        }, status=400)

    # === CASH ON DELIVERY → status = completed ===
    order_status = "placed" if payment_method == "cod" else "pending"
    with transaction.atomic():
        # Create Order
        total = sum(item.subtotal() for item in cart_items)
        order = Order.objects.create(
            user=request.user,
            address=address,
            payment_method=payment_method,
            status=order_status,
            total_amount=total
        )

        # Create Payment object with pending status
        Payment.objects.create(
            order=order,
            user=request.user,
            payment_method=payment_method,
            amount=total,
            status='pending'
        )


        # Create OrderItems
        order_items = []
        for cart_item in cart_items:
            order_items.append(
                OrderItem(
                    order=order,
                    product=cart_item.product,
                    size=cart_item.size,
                    preference=cart_item.preference,
                    quantity=cart_item.quantity,
                    price_at_purchase=cart_item.price_at_addition
                )
            )

        OrderItem.objects.bulk_create(order_items)

        # Empty cart
        cart_items.delete()


    return JsonResponse({
        "success": True,
        "message": "Order placed successfully!",
        "order_id": order.id,
        "status": order.status,
        "total": float(order.total_amount)
    })



def shop(request):
    query = request.GET.get('q')
    products = Product.objects.filter(status='active')
    categories = Category.objects.all() 
    veg_products = Product.objects.all()
    non_veg_products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(category__name__icontains=query)
        )

    products = products.order_by('-created_at')

    def format_products_with_sizes(products):
        product_list = []
        for product in products:
            size_data = []
            for size in product.sizes.all():
                size_data.append({
                    'size': size.size,
                    'price': float(size.price),
                    'discounted_price': float(size.discounted_price) if size.discounted_price else None,
                })
            product_list.append({
                'id': product.id,
                'name': product.name,
                'image': product.image.url if product.image else '',
                'category': product.category.name if product.category else '',
                'in_stock': product.in_stock,
                'slug': product.slug,
                'stock_count': getattr(product, 'stock_count', 0),
                'sizes': size_data,
            })
        return product_list

    context = {
        'products': format_products_with_sizes(products),
        'veg_products': veg_products,
        'non_veg_products': non_veg_products,
        'categories': categories,
        'query': query
    }

    return render(request, 'frontend/shop.html', context)

def aboutus(request):
    products = Product.objects.filter(status='active').order_by('-created_at')
    categories = Category.objects.all() 
    veg_products = Product.objects.all()
    non_veg_products = Product.objects.all()

    return render(request, 'frontend/aboutus.html', {
        'veg_products': veg_products,
        'non_veg_products': non_veg_products,
        'products': products,
        'categories': categories
    })

def contactus(request):
    products = Product.objects.filter(status='active').order_by('-created_at')
    categories = Category.objects.all() 
    veg_products = Product.objects.all()
    non_veg_products = Product.objects.all()
    return render(request, 'frontend/contactus.html', {
        'veg_products': veg_products,
        'non_veg_products': non_veg_products,
        'products': products,
        'categories': categories
    })

def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        username = email 
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user) 
            toast.success(request, f"Welcome back, {user.first_name}!")
            return redirect('/') 
        else:
            toast.error(request, "Invalid credentials. Please try again.")
    return render(request, 'frontend/login.html')


def signin(request):
    if request.method == 'POST':
        first_name = request.POST.get('firstname')
        last_name = request.POST.get('lastname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        username = email 
        
        if User.objects.filter(email=email).exists():
            toast.error(request, "Email already registered!")
            return render(request, 'frontend/signin.html')
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            user.save()
           
            toast.success(request, "Account created successfully! Please log in.")
            return redirect('login')
            
        except Exception as e:
            toast.error(request, f"An error occurred during registration: {e}")
    return render(request, 'frontend/signin.html')

def logout_user(request):
    if request.user.is_authenticated:
        logout(request)
        toast.success(request, "You have been logged out successfully.")
    return redirect('login') # Redirect to login page after logout

def privacy_policy(request):
    products = Product.objects.filter(status='active').order_by('-created_at')
    categories = Category.objects.all() 
    veg_products = Product.objects.all()
    non_veg_products = Product.objects.all()

    return render(request, 'frontend/privacy.and.policy.html', {
        'veg_products': veg_products,
        'non_veg_products': non_veg_products,
        'products': products,
        'categories': categories
    })

def shipping_policy(request):
    products = Product.objects.filter(status='active').order_by('-created_at')
    categories = Category.objects.all() 
    veg_products = Product.objects.all()
    non_veg_products = Product.objects.all()

    return render(request, 'frontend/shipping-policy.html', {
        'veg_products': veg_products,
        'non_veg_products': non_veg_products,
        'products': products,
        'categories': categories
    })

def returnandrefund_policy(request):
    products = Product.objects.filter(status='active').order_by('-created_at')
    categories = Category.objects.all() 
    veg_products = Product.objects.all()
    non_veg_products = Product.objects.all()

    return render(request, 'frontend/returnandrefund.html', {
        'veg_products': veg_products,
        'non_veg_products': non_veg_products,
        'products': products,
        'categories': categories
    })

def cancellation_policy(request):
    products = Product.objects.filter(status='active').order_by('-created_at')
    categories = Category.objects.all() 
    veg_products = Product.objects.all()
    non_veg_products = Product.objects.all()

    return render(request, 'frontend/cancellation.html', {
        'veg_products': veg_products,
        'non_veg_products': non_veg_products,
        'products': products,
        'categories': categories
    })


@login_required(login_url='login') 
def profile_page(request):
    products = Product.objects.filter(status='active').order_by('-created_at')
    categories = Category.objects.all() 
    veg_products = Product.objects.all()
    non_veg_products = Product.objects.all()
    cart_count = Cart.objects.filter(user=request.user).count()
    user_orders_count = request.user.orders.count()  # count orders related to logged-in user



    return render(request, 'frontend/profile-page.html', {
        'veg_products': veg_products,
        'non_veg_products': non_veg_products,
        'products': products,
        'categories': categories,
        'cart_count': cart_count,
        'user_orders_count': user_orders_count,

    })

@login_required(login_url='login') 
def orders_page(request):
    # Get user's orders with related items
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')

    # Common context (keep your existing sidebar data)
    products = Product.objects.filter(status='active').order_by('-created_at')
    categories = Category.objects.all()
    cart_count = Cart.objects.filter(user=request.user).count()

    return render(request, 'frontend/orders-page.html', {
        'orders': orders,
        'veg_products': Product.objects.all(),
        'non_veg_products': Product.objects.all(),
        'products': products,
        'categories': categories,
        'cart_count': cart_count
    })


@login_required(login_url='login') 
def logout_page(request):
    products = Product.objects.filter(status='active').order_by('-created_at')
    categories = Category.objects.all() 
    veg_products = Product.objects.all()
    non_veg_products = Product.objects.all()
    cart_count = Cart.objects.filter(user=request.user).count()


    return render(request, 'frontend/logout-page.html', {
        'veg_products': veg_products,
        'non_veg_products': non_veg_products,
        'products': products,
        'categories': categories,
        'cart_count': cart_count
    })

@login_required(login_url='login') 
def address_profile(request):    
    products = Product.objects.filter(status='active').order_by('-created_at')
    categories = Category.objects.all() 
    veg_products = Product.objects.all()
    non_veg_products = Product.objects.all()
    cart_count = Cart.objects.filter(user=request.user).count()
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')

    return render(request, 'frontend/address-page.html', {
        'veg_products': veg_products,
        'non_veg_products': non_veg_products,
        'products': products,
        'categories': categories,
        'cart_count': cart_count,
        'addresses': addresses,
    })

@csrf_exempt
@login_required(login_url='login') 
def create_address(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if data.get('is_default'):
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        address = Address.objects.create(
            user=request.user,
            first_name=data['first_name'],
            last_name=data['last_name'],
            mobile_number=data['mobile_number'],  # Added mobile number
            address_type=data['address_type'],
            address_line_one=data['address_line_one'],
            address_line_two=data.get('address_line_two', ''),
            city=data['city'],
            zip_code=data['zip_code'],
            is_default=data.get('is_default', False)
        )
        return JsonResponse({
            'id': address.id,
            'first_name': address.first_name,
            'last_name': address.last_name,
            'mobile_number': address.mobile_number,  # Added mobile number
            'address_type': address.get_address_type_display(),
            'address_line_one': address.address_line_one,
            'address_line_two': address.address_line_two,
            'city': address.city,
            'zip_code': address.zip_code,
            'is_default': address.is_default
        })
    return JsonResponse({'error': 'Invalid request method'})

@login_required(login_url='login') 
def get_address(request, pk):
    address = get_object_or_404(Address, id=pk, user=request.user)
    data = {
        "first_name": address.first_name,
        "last_name": address.last_name,
        "mobile_number": address.mobile_number,  # Added mobile number
        "address_type": address.address_type,
        "address_line_one": address.address_line_one,
        "address_line_two": address.address_line_two,
        "city": address.city,
        "zip_code": address.zip_code,
        "is_default": address.is_default,
    }
    return JsonResponse(data)

@login_required(login_url='login') 
def update_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        data = json.loads(request.body)
        address.first_name = data['first_name']
        address.last_name = data['last_name']
        address.mobile_number = data['mobile_number']  # Added mobile number
        address.address_type = data['address_type']
        address.address_line_one = data['address_line_one']
        address.address_line_two = data.get('address_line_two', '')
        address.city = data['city']
        address.zip_code = data['zip_code']
        address.is_default = data.get('is_default', False)

        if address.is_default:
            Address.objects.filter(user=request.user, is_default=True).exclude(id=pk).update(is_default=False)

        address.save()

        return JsonResponse({
            'id': address.id,
            'first_name': address.first_name,
            'last_name': address.last_name,
            'mobile_number': address.mobile_number,  # Added mobile number
            'address_type': address.get_address_type_display(),
            'address_line_one': address.address_line_one,
            'address_line_two': address.address_line_two,
            'city': address.city,
            'zip_code': address.zip_code,
            'is_default': address.is_default
        })

@login_required(login_url='login') 
def delete_address(request, pk):
    Address.objects.filter(id=pk, user=request.user).delete()
    return JsonResponse({'success': True})

@login_required(login_url='login') 
def set_default_address(request, pk):
    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
    Address.objects.filter(id=pk, user=request.user).update(is_default=True)
    return JsonResponse({'success': True})

@login_required(login_url='login') 
def update_profile(request):
    products = Product.objects.filter(status='active').order_by('-created_at')
    categories = Category.objects.all() 
    veg_products = Product.objects.all()
    non_veg_products = Product.objects.all()
    cart_count = Cart.objects.filter(user=request.user).count()
    cart_count = Cart.objects.filter(user=request.user).count()

    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user
        error = None

        # Update username and email
        if username:
            user.username = username
        if email:
            user.email = email

        # Update password if fields are filled
        if current_password or new_password or confirm_password:
            if not user.check_password(current_password):
                error = "Current password is incorrect."
            elif new_password != confirm_password:
                error = "New passwords do not match."
            else:
                user.set_password(new_password)
                update_session_auth_hash(request, user)  # Keep user logged in after password change

        if error:
            messages.error(request, error)
        else:
            user.save()
            messages.success(request, "Profile updated successfully!")

    return render(request, 'frontend/update-profile.html', {
        'veg_products': veg_products,
        'non_veg_products': non_veg_products,
        'products': products,
        'categories': categories,
        'cart_count': cart_count,
        'user': request.user,
    })

@login_required(login_url='login') 
def profile(request):
    return render(request, 'frontend/profile.html', {'user': request.user})

@login_required(login_url='login') 
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keeps the user logged in
            return JsonResponse({'success': True})
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'errors': errors})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def add_to_cart_ajax(request):
    return 

def terms_and_conditions(request):
    products = Product.objects.filter(status='active').order_by('-created_at')
    categories = Category.objects.all() 
    veg_products = Product.objects.all()
    non_veg_products = Product.objects.all()

    return render(request, 'frontend/termsandconditions.html', {
        'veg_products': veg_products,
        'non_veg_products': non_veg_products,
        'products': products,
        'categories': categories
    })




def adminlogin_page(request):

    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('dashboard')
        elif not request.user.is_superuser:
            return redirect('/')

    if request.method == 'POST':
        print("coming here")

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        print("Username:", username)
        print("Password:", password)
        print(user)

        if user is not None:
            login(request, user)
            toast.success(request, f"Welcome back, {user.first_name}!")
            return redirect('dashboard')
        else:
            toast.error(request, "Invalid credentials. Please try again.")

    return render(request, 'backend/login.html')

def adminlogout_page(request):
    if request.user.is_authenticated:
        logout(request)
        toast.success(request, "You have been logged out successfully.")
    return redirect('adminlogin')
@login_required(login_url='adminlogin')
def dashboard(request):
    if request.user.is_superuser:
        return render(request, 'backend/dashboard.html')
    else:
        return redirect('home')


@login_required(login_url='adminlogin')
def categories(request, slug=None):
    if request.user.is_superuser:
        categories = Category.objects.all().order_by('priority')
        category = None

        if slug:
            category = get_object_or_404(Category, slug=slug)

        if request.method == 'POST':
            if category:
                form = CategoryForm(request.POST, request.FILES, instance=category)
            else:
                form = CategoryForm(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                toast.success(request, 'Category updated successfully!' if category else 'Category created successfully!')
                return redirect('categories')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        toast.error(request, f"{field}: {error}")

        elif request.method == 'GET' and 'delete' in request.path and category:
            category.delete()
            toast.success(request, 'Category deleted successfully!')
            return redirect('categories')

        else:
            form = CategoryForm(instance=category)

        return render(request, 'backend/categories.html', {
            'form': form,
            'categories': categories,
            'edit_mode': bool(category),
        })
    else:
        return redirect('home')
    

@login_required(login_url='adminlogin')
def delete_product_image(request, image_id):
    if request.user.is_superuser:
        if request.method == "POST":
            try:
                image = ProductImage.objects.get(id=image_id)
                image.delete()
                return JsonResponse({'success': True})
            except ProductImage.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Image not found'})
        return HttpResponseNotFound()
    else:
        return redirect('home')
@login_required(login_url='adminlogin')
def products(request):
    if request.user.is_superuser:
        product_list = Product.objects.all()
        return render(request, 'backend/products.html', {'products': product_list})
    else:
        return redirect('home')
@login_required(login_url='adminlogin')
def create_product(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            product_form = ProductForm(request.POST, request.FILES)

            if product_form.is_valid():
                product = product_form.save()

                sizes = ['250 ml', '500 ml', '750 ml', '1 L']
                for size in sizes:
                    price = request.POST.get(f'price_{size}', None)
                    discounted_price = request.POST.get(f'discounted_price_{size}', None)
                    if price:
                        ProductSize.objects.create(
                            product=product,
                            size=size,
                            price=price,
                            discounted_price=discounted_price or 0
                        )

                images = request.FILES.getlist('images')
                for img in images:
                    ProductImage.objects.create(product=product, image=img)

                messages.success(request, "Product created successfully!")
                return redirect('products')
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            product_form = ProductForm()

        for field_name, field in product_form.fields.items():
            existing_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_classes} form-control'.strip()

        return render(request, 'backend/create_product.html', {
            'form': product_form,
            'sizes': ['250ml', '500ml', '750ml', '1L'],
        })
    else:
        return redirect('home')
    
@login_required(login_url='adminlogin')
def edit_product(request, slug):
    if request.user.is_superuser:
        product = get_object_or_404(Product, slug=slug)
        images = ProductImage.objects.filter(product=product)

        if request.method == 'POST':
            form = ProductForm(request.POST, request.FILES, instance=product)
            files = request.FILES.getlist('images')

            if form.is_valid():
                form.save()

                # Add new images
                for file in files:
                    ProductImage.objects.create(product=product, image=file)

                messages.success(request, "Product updated successfully!")
                return redirect('products')
            else:
                messages.error(request, "Please fix the errors below.")
        else:
            form = ProductForm(instance=product)

        return render(request, 'backend/product_edit.html', {
            'form': form,
            'product': product,
            'images': images
        })
    else:
        return redirect('home')
    
@login_required(login_url='adminlogin')
def delete_product(request, slug):
    if request.user.is_superuser:
        try:
            product = Product.objects.get(slug=slug)
            product.delete()
            return JsonResponse({'success': True})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'})
    else:
        return redirect('home')

@login_required(login_url='adminlogin')
def order_checkout(request):
    if request.user.is_superuser:
        return render(request, 'backend/order-checkout.html')
    else:
        return redirect('home')
@login_required(login_url='adminlogin')
def order_detail(request, pk):
    if request.user.is_superuser:
        order = get_object_or_404(Order, pk=pk)
        return render(request, 'backend/order-detail.html', {'order': order})
    else:
        return redirect('home')
    

@login_required(login_url='adminlogin')
def orders_list(request):
    if request.user.is_superuser:
        orders = Order.objects.exclude(status='pending').prefetch_related('payments')
        return render(request, 'backend/orders-list.html', {'orders': orders})
    else:
        return redirect('home')



@login_required(login_url='adminlogin')
def collect_cash(request, order_id):

    if request.user.is_superuser:

        order = get_object_or_404(Order, id=order_id)
        order.status = 'delivered'
        order.save()

        try:
            payment = Payment.objects.get(order=order)
            payment.status = "success"
            payment.save()
        except Payment.DoesNotExist:
            pass

        # redirect back to same page
        return redirect(request.META.get('HTTP_REFERER', 'orders_list'))

    else:
        return redirect('home')
    


    

@login_required(login_url='adminlogin')
def product_add(request):
    if request.user.is_superuser:
        return render(request, 'backend/product-add.html')
    else:
        return redirect('home')
@login_required(login_url='adminlogin')
def product_details(request):
    if request.user.is_superuser:
        return render(request, 'backend/product-details.html')
    else:
        return redirect('home')
@login_required(login_url='adminlogin')
def product_edit(request):
    if request.user.is_superuser:
        return render(request, 'backend/product-edit.html')
    else:
        return redirect('home')
@login_required(login_url='adminlogin')
def product_list(request):
    if request.user.is_superuser:
        return render(request, 'backend/product-list.html')
    else:
        return redirect('home')




@login_required(login_url='adminlogin')
def payment_list(request):

    if request.user.is_superuser:

        payments = Payment.objects.filter(status='success').select_related(
            'order','user'
        ).prefetch_related(
            'order__items',
            'order__items__product'
        )

        return render(request,'backend/payment-list.html',{
            'payments':payments
        })

    else:
        return redirect('home')


@login_required(login_url='adminlogin')
def purchase_order(request):
    if request.user.is_superuser:
        return render(request, 'backend/purchase-order.html')
    else:
        return redirect('home')
@login_required(login_url='adminlogin')
def purchase_returns(request):
    if request.user.is_superuser:
        return render(request, 'backend/purchase-returns.html')
    else:
        return redirect('home')
@login_required(login_url='adminlogin')
def settings(request):
    if request.user.is_superuser:
        return render(request, 'backend/settings.html')
    else:
        return redirect('home')
