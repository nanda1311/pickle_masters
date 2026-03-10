from django import forms
from .models import *
from .models import Banner, STATUS_CHOICES
from .models import Product
from tinymce.widgets import TinyMCE
from taggit.forms import TagWidget

from .models import Product
from django.forms import inlineformset_factory
from rest_framework import serializers


class AddressSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='__str__', read_only=True)

    class Meta:
        model = Address
        fields = [
            'slug', 'first_name', 'last_name', 'address_type', 'mobile_number',
            'address_line_one', 'address_line_two', 'city', 'zip_code',
            'is_default', 'full_name'
        ]

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name','priority', 'slug', 'parent_category', 'status']



class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'image', 'category', 'in_stock', 'stock_count',
            'status', 'ingredients', 'nutrition_info'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'in_stock': forms.Select(attrs={'class': 'form-control'}),
            'stock_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'ingredients': forms.Textarea(attrs={'class': 'form-control', 'id': 'id_ingredients'}),
            'nutrition_info': forms.Textarea(attrs={'class': 'form-control', 'id': 'id_nutrition_info'}),
        }


class ProductSizeForm(forms.ModelForm):
    class Meta:
        model = ProductSize
        fields = ['size', 'price', 'discounted_price']

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']