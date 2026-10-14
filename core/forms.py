from django import forms
from .models import *
from .models import Banner, STATUS_CHOICES
from .models import Product
from tinymce.widgets import TinyMCE
from taggit.forms import TagWidget

from .models import Product
from django.forms import inlineformset_factory
from rest_framework import serializers

from django import forms


class PincodeCheckForm(forms.Form):
    pincode = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter Pincode"
            }
        )
    )

    def clean_pincode(self):
        pincode = self.cleaned_data["pincode"]

        if not pincode.isdigit():
            raise forms.ValidationError("Enter a valid pincode.")

        return pincode


    
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
    discounted_price = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Optional discount price',
        }),
    )

    class Meta:
        model = ProductSize
        fields = ['size', 'price', 'discounted_price']
        widgets = {
            'size': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Regular price',
            }),
        }


ProductSizeFormSet = inlineformset_factory(
    Product,
    ProductSize,
    form=ProductSizeForm,
    extra=1,
    can_delete=True,
)

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']