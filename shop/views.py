from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Category, Product, Cart, CartItem, Order, OrderItem, UserProfile
from .forms import UserRegisterForm, UserLoginForm, UserProfileForm, CheckoutForm


def home(request):
    """صفحه اصلی"""
    featured_products = Product.objects.filter(is_featured=True, available=True)[:8]
    categories = Category.objects.all()[:6]
    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, 'shop/home.html', context)


def product_list(request, category_slug=None):
    """لیست محصولات"""
    category = None
    products = Product.objects.filter(available=True)
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Search
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Filter by price
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sort
    sort = request.GET.get('sort', '-created_at')
    if sort in ['price', '-price', 'name', '-created_at']:
        products = products.order_by(sort)
    
    categories = Category.objects.all()
    
    context = {
        'category': category,
        'products': products,
        'categories': categories,
        'query': query,
    }
    return render(request, 'shop/product_list.html', context)


def product_detail(request, slug):
    """جزئیات محصول"""
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(
        category=product.category, 
        available=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'shop/product_detail.html', context)


@login_required
def cart_view(request):
    """نمایش سبد خرید"""
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
    context = {'cart': cart}
    return render(request, 'shop/cart.html', context)


@login_required
def add_to_cart(request, product_id):
    """افزودن به سبد خرید"""
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
    
    size = request.POST.get('size', '')
    color = request.POST.get('color', '')
    quantity = int(request.POST.get('quantity', 1))
    
    # Check if item already exists
    cart_item = CartItem.objects.filter(
        cart=cart, 
        product=product, 
        size=size, 
        color=color
    ).first()
    
    if cart_item:
        cart_item.quantity += quantity
        cart_item.save()
    else:
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=quantity,
            size=size,
            color=color
        )
    
    messages.success(request, f'{product.name} به سبد خرید اضافه شد.')
    return redirect('shop:cart')


@login_required
def update_cart_item(request, item_id):
    """به‌روزرسانی تعداد آیتم سبد"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    
    return redirect('shop:cart')


@login_required
def remove_from_cart(request, item_id):
    """حذف از سبد خرید"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'محصول از سبد خرید حذف شد.')
    return redirect('shop:cart')


@login_required
def checkout(request):
    """صفحه تسویه حساب"""
    cart = Cart.objects.filter(user=request.user, is_active=True).first()
    
    if not cart or cart.items.count() == 0:
        messages.warning(request, 'سبد خرید شما خالی است.')
        return redirect('shop:cart')
    
    # Get user profile for pre-filling form
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_price = cart.get_total_price()
            order.status = 'pending'
            order.save()
            
            # Create order items from cart
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.get_final_price(),
                    size=item.size,
                    color=item.color
                )
            
            # Clear cart
            cart.is_active = False
            cart.save()
            
            messages.success(request, f'سفارش شما با موفقیت ثبت شد. شماره سفارش: {order.id}')
            return redirect('shop:order_detail', order_id=order.id)
    else:
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'phone': profile.phone,
            'address': profile.address,
            'city': profile.city,
            'postal_code': profile.postal_code,
        }
        form = CheckoutForm(initial=initial_data)
    
    context = {
        'cart': cart,
        'form': form,
    }
    return render(request, 'shop/checkout.html', context)


@login_required
def order_detail(request, order_id):
    """جزئیات سفارش"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {'order': order}
    return render(request, 'shop/order_detail.html', context)


@login_required
def user_profile(request):
    """پروفایل کاربر"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'پروفایل شما با موفقیت به‌روزرسانی شد.')
            return redirect('shop:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'form': form,
        'orders': orders,
    }
    return render(request, 'shop/profile.html', context)


def register(request):
    """ثبت‌نام کاربر"""
    if request.user.is_authenticated:
        return redirect('shop:home')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, f'خوش آمدید {user.username}! حساب کاربری شما ایجاد شد.')
            return redirect('shop:home')
    else:
        form = UserRegisterForm()
    
    return render(request, 'registration/register.html', {'form': form})


def user_login(request):
    """ورود کاربر"""
    if request.user.is_authenticated:
        return redirect('shop:home')
    
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'خوش آمدید {user.username}!')
            next_url = request.GET.get('next', 'shop:home')
            return redirect(next_url)
    else:
        form = UserLoginForm()
    
    return render(request, 'registration/login.html', {'form': form})


def user_logout(request):
    """خروج کاربر"""
    logout(request)
    messages.success(request, 'شما با موفقیت خارج شدید.')
    return redirect('shop:home')
