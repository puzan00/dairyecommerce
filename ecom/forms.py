from django import forms
from django.contrib.auth.models import User
from . import models


class CustomerUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=True)  # Make password optional

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "password"]
        profile_pic = forms.ImageField(required=True)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username
class CustomerForm(forms.ModelForm):
    class Meta:
        model = models.Customer
        fields = ["address", "mobile", "profile_pic"]
        profile_pic = forms.ImageField(required=True)
class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username"]  # Exclude password field

class EditCustomerForm(forms.ModelForm):
    class Meta:
        model = models.Customer
        fields = ["address", "mobile", "profile_pic"]  # Keep customer-related fields for updating
        profile_pic = forms.ImageField(required=True)
class ProductForm(forms.ModelForm):
    class Meta:
        model = models.Product
        fields = [
            "name",
            "price",
            "description",
            "product_image",
            "quantity",
            "unit",
            "expiry_date",
        ]
        expiry_date = forms.DateField(required=True)

# address of shipment
class AddressForm(forms.Form):
    Email = forms.EmailField()
    Mobile =forms.CharField(min_length=10,max_length=10, required=True)
    Address = forms.CharField(max_length=500)



# for updating status of order
class OrderForm(forms.ModelForm):
    class Meta:
        model = models.Orders
        fields = ["status"]



    