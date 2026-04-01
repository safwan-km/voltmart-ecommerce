from django import forms
from products.models import Product
from products.models import Category,HeroBanner
from orders.models import Coupon

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "category",
            "name",
            "description",
            "price",
            "stock",
            "image",
            "is_active",
            "is_featured",
        ]

        widgets = {
            "category": forms.Select(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4
            }),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "stock": forms.NumberInput(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={}),
            "is_featured": forms.CheckboxInput(attrs={}),
        }
        
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "is_active","image","is_featured"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "is_featured": forms.CheckboxInput(),
        }


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            "code",
            "discount_type",
            "discount_value",
            "expiry_date",
            "per_user_limit",
            "is_active",
        ]

        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "discount_type": forms.Select(attrs={"class": "form-control"}),
            "discount_value": forms.NumberInput(attrs={"class": "form-control"}),
            "expiry_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "per_user_limit": forms.NumberInput(attrs={"class": "form-control"}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["expiry_date"].required = False
        
        

class HeroBannerForm(forms.ModelForm):
    class Meta:
        model = HeroBanner
        fields = [
            'title',
            'subtitle',
            'image',
            'is_active',
            'theme',
            'product',     
        ]