from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin
# from .models import CustomUser

# Register your models here.
admin.site.register(Banner)
# admin.site.register(Message)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ProductSize)
admin.site.register(ServiceablePincode)
# admin.site.register(Profile)
