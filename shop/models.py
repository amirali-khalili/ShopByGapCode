import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Category(models.Model):
    """دسته‌بندی محصولات"""
    name = models.CharField(max_length=200, verbose_name='نام دسته‌بندی')
    slug = models.SlugField(max_length=200, unique=True, allow_unicode=True)
    description = models.TextField(blank=True, verbose_name='توضیحات')
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='تصویر')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_list_by_category', args=[self.slug])


class Product(models.Model):
    """محصول پوشاک"""
    SIZE_CHOICES = [
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                  related_name='products', verbose_name='دسته‌بندی')
    name = models.CharField(max_length=200, verbose_name='نام محصول')
    slug = models.SlugField(max_length=200, unique=True, allow_unicode=True)
    description = models.TextField(verbose_name='توضیحات')
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='قیمت (تومان)')
    discount_price = models.DecimalField(max_digits=12, decimal_places=0,
                                          blank=True, null=True, verbose_name='قیمت با تخفیف')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='تصویر اصلی')
    image2 = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='تصویر دوم')
    image3 = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='تصویر سوم')
    stock = models.PositiveIntegerField(default=0, verbose_name='موجودی')
    available = models.BooleanField(default=True, verbose_name='موجود')
    sizes = models.CharField(max_length=50, blank=True, verbose_name='سایزهای موجود',
                              help_text='مثال: S,M,L,XL')
    colors = models.CharField(max_length=200, blank=True, verbose_name='رنگ‌های موجود',
                               help_text='مثال: قرمز,آبی,سبز')
    is_featured = models.BooleanField(default=False, verbose_name='ویژه')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.slug])

    def get_final_price(self):
        return self.discount_price if self.discount_price else self.price

    def get_discount_percent(self):
        if self.discount_price and self.price > 0:
            return int((1 - self.discount_price / self.price) * 100)
        return 0

    def get_sizes_list(self):
        return [s.strip() for s in self.sizes.split(',') if s.strip()]

    def get_colors_list(self):
        return [c.strip() for c in self.colors.split(',') if c.strip()]


class UserProfile(models.Model):
    """پروفایل کاربر"""
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                 related_name='profile', verbose_name='کاربر')
    phone = models.CharField(max_length=15, blank=True, verbose_name='شماره تلفن')
    address = models.TextField(blank=True, verbose_name='آدرس')
    city = models.CharField(max_length=100, blank=True, verbose_name='شهر')
    postal_code = models.CharField(max_length=10, blank=True, verbose_name='کد پستی')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='عکس پروفایل')

    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل‌های کاربران'

    def __str__(self):
        return f'پروفایل {self.user.username}'


class Cart(models.Model):
    """سبد خرید"""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='carts', verbose_name='کاربر')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'سبد خرید'
        verbose_name_plural = 'سبدهای خرید'

    def __str__(self):
        return f'سبد خرید {self.user.username}'

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def get_items_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """آیتم سبد خرید"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE,
                              related_name='items', verbose_name='سبد خرید')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='محصول')
    quantity = models.PositiveIntegerField(default=1, verbose_name='تعداد')
    size = models.CharField(max_length=10, blank=True, verbose_name='سایز')
    color = models.CharField(max_length=50, blank=True, verbose_name='رنگ')

    class Meta:
        verbose_name = 'آیتم سبد'
        verbose_name_plural = 'آیتم‌های سبد'

    def __str__(self):
        return f'{self.quantity} عدد {self.product.name}'

    def get_total_price(self):
        return self.product.get_final_price() * self.quantity


class Order(models.Model):
    """سفارش"""
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('processing', 'در حال پردازش'),
        ('shipped', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
        ('cancelled', 'لغو شده'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='orders', verbose_name='کاربر')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                               default='pending', verbose_name='وضعیت')
    first_name = models.CharField(max_length=100, verbose_name='نام')
    last_name = models.CharField(max_length=100, verbose_name='نام خانوادگی')
    phone = models.CharField(max_length=15, verbose_name='شماره تلفن')
    address = models.TextField(verbose_name='آدرس')
    city = models.CharField(max_length=100, verbose_name='شهر')
    postal_code = models.CharField(max_length=10, verbose_name='کد پستی')
    notes = models.TextField(blank=True, verbose_name='توضیحات سفارش')
    total_price = models.DecimalField(max_digits=12, decimal_places=0,
                                       verbose_name='مبلغ کل')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارش‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f'سفارش #{self.id} - {self.user.username}'


class OrderItem(models.Model):
    """آیتم سفارش"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                               related_name='items', verbose_name='سفارش')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='محصول')
    quantity = models.PositiveIntegerField(default=1, verbose_name='تعداد')
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='قیمت واحد')
    size = models.CharField(max_length=10, blank=True, verbose_name='سایز')
    color = models.CharField(max_length=50, blank=True, verbose_name='رنگ')

    class Meta:
        verbose_name = 'آیتم سفارش'
        verbose_name_plural = 'آیتم‌های سفارش'

    def __str__(self):
        return f'{self.quantity} عدد {self.product.name}'

    def get_total_price(self):
        return self.price * self.quantity
