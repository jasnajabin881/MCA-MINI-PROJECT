from django import forms
from .models import *

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',  # Add Bootstrap class for form control
            'placeholder': 'Enter password'  # Optional: Add placeholder text
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',  # Add Bootstrap class for form control
            'placeholder': 'Enter email'  # Optional: Add placeholder text
        })
    )

    class Meta:
        model = User
        fields = ['email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class SellerRegistrationForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your name'})
    )
    business_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter business name'})
    )
    tax_info = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tax info'})
    )
    location = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location'})
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter address'})
    )

    class Meta:
        model = User
        fields = ['email', 'password', 'name', 'business_name', 'tax_info', 'location', 'address']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_seller = True  # Mark the user as a seller
        if commit:
            user.save()
            seller_profile = SellerProfile.objects.create(
                user=user,
                name=self.cleaned_data['name'],
                business_name=self.cleaned_data['business_name'],
                tax_info=self.cleaned_data['tax_info'],
                location=self.cleaned_data['location'],
                address=self.cleaned_data['address']
            )
            seller_profile.save()
        return user


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'commission', 'status']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'category', 'sku', 'thumbnail', 'image', 'image1', 
            'image2', 'image3', 'stock', 'discount', 'weight', 'dimensions', 
            'shipping_charge', 'tax_percentage', 'offer', 'status'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Product Description'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SKU'}),
            'thumbnail': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'image1': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'image2': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'image3': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Stock Quantity'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Discount'}),
            'weight': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Weight'}),
            'dimensions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dimensions'}),
            'shipping_charge': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Shipping Charge'}),
            'tax_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Tax Percentage'}),
            'offer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Offer'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']


from django import forms
from .models import UserProfile

class ShippingForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }
