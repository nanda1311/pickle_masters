from django.db import models
from django.utils.text import slugify
from tinymce.models import HTMLField
from django.db import models
import uuid
from tinymce.models import HTMLField
from django.utils.text import slugify
from taggit.managers import TaggableManager
from multiselectfield import MultiSelectField
from django.contrib.auth.models import User


class ServiceablePincode(models.Model):
    pincode = models.CharField(max_length=6, unique=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["pincode"]

    def __str__(self):
        return f"{self.pincode} - {self.city}"

CATEGORY_STATUS = (
    ('active', 'Active'),
    ('inactive', 'Inactive'),
)


STATUS_CHOICES = (
    ('active', 'Active'),
    ('inactive', 'Inactive'),
)
# Create your models here.
class Banner(models.Model):

     COLOR_CHOICES = [
          ('black','black'),
          ('white','white'),
     ]
     heading = models.CharField(max_length=250,blank=True, null=True)
     description = models.TextField(blank=True, null=True)
     button_text = models.CharField(max_length=100,blank=True, null=True)
     button_url = models.URLField(blank=True, null=True)
     created_at = models.DateTimeField(auto_now_add=True)
     updated_at = models.DateTimeField(auto_now=True)
     image_for_desktop = models.FileField(upload_to='banners/desktop')
     image_for_mobile = models.FileField(upload_to='banners/desktop')
     status = models.BooleanField(default=True)
     color = models.CharField(max_length=10, choices=COLOR_CHOICES, default='black')

     def __str__(self):
          return self.heading

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    priority= models.IntegerField(default=100)
    parent_category = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    status = models.CharField(max_length=10, choices=CATEGORY_STATUS, default='active')
    slug = models.SlugField(unique=True, blank=True)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_products = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True,blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name





class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ]

    STOCK_CHOICES = [
        ('in_stock', 'In Stock'),
        ('out_of_stock', 'Out Of Stock')
    ]

    product_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    image = models.FileField(upload_to='category_images/', null=True, blank=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE, null=True, blank=True)
    in_stock = models.CharField(max_length=20, choices=STOCK_CHOICES, default='in_stock')
    stock_count = models.PositiveIntegerField(default=0) 
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='active')
    ingredients = HTMLField(null=True, blank=True, verbose_name="Ingredients")
    nutrition_info = HTMLField(null=True, blank=True, verbose_name="Nutrition Information")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)


    def get_default_price(self):
        size = self.sizes.first()
        if size:
            return size.discounted_price or size.price
        return 0
        
    def save(self, *args, **kwargs):
        if self.in_stock == 'out_of_stock':
            self.stock_count = 0

        if not self.pk and not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug
            num = 1
            while Product.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductSize(models.Model):
    SIZE_CHOICES = [
        ('250 grms', '250 grms'),
        ('500 grms', '500 grms'),
        ('750 grms', '750 grms'),
        ('1 kg', '1 kg'),
    ]

    product = models.ForeignKey(Product, related_name='sizes', on_delete=models.CASCADE)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.size}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} Image"
    
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Address(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('home', 'Home'),
        ('office', 'Office'),
        ('other', 'Other'),
    ]

    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='home')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)  # Added mobile number field
    address_line_one = models.CharField(max_length=255, blank=True, null=True)
    address_line_two = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    is_default = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            slug_base = f"{self.user.username}-{self.address_line_one}"
            unique_slug = slugify(slug_base)
            counter = 1
            
            while Address.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{slugify(slug_base)}-{counter}"
                counter += 1

            self.slug = unique_slug

        super(Address, self).save(*args, **kwargs)

    def full_address(self):
        address_parts = [self.address_line_one]

        if self.address_line_two:
            address_parts.append(self.address_line_two)
        if self.city:
            address_parts.append(self.city)
        if self.zip_code:
            address_parts.append(self.zip_code)

        return ', '.join(filter(None, address_parts))

    def __str__(self):
        return f"{self.first_name} {self.last_name}'s Address in {self.city}"
    

class ProductPreference(models.Model):
    product = models.ForeignKey(Product, related_name='preferences',
    on_delete=models.CASCADE)
    name = models.CharField(max_length=50)       
    extra_price = models.DecimalField(max_digits=6, decimal_places=2,
    default=0.00)  

    def __str__(self):
        return f"{self.product.name} – {self.name}"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    size = models.CharField(max_length=50, blank=True, null=True)
    preference = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price_at_addition = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    added_at = models.DateTimeField(auto_now_add=True)

    def subtotal(self):
        return self.quantity * self.price_at_addition

    def __str__(self):
        return f"{self.product.name} ({self.size}) - {self.user.username}"
    

from django.utils import timezone

class Order(models.Model):
    PAYMENT_CHOICES = (
        ('cod', 'Cash on Delivery'),
        ('online', 'Online'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('placed', 'Placed'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
   
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=50)
    preference = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantity * self.price_at_purchase

    def __str__(self):
        return f"{self.product.name} ({self.size}) x{self.quantity}"








class Payment(models.Model):

    PAYMENT_METHODS = (
        ('cod', 'Cash on Delivery'),
        ('online', 'Online'),
    )

    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=200, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order.order_id} - {self.payment_method}"