from django import forms
from django.contrib.auth.models import User
from . import models


class CustomerUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)  # Make password optional

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "password"]



class CustomerForm(forms.ModelForm):
    class Meta:
        model = models.Customer
        fields = ["address", "mobile", "profile_pic"]

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username"]  # Exclude password field

class EditCustomerForm(forms.ModelForm):
    class Meta:
        model = models.Customer
        fields = ["address", "mobile", "profile_pic"]  # Keep customer-related fields for updating

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


# address of shipment
class AddressForm(forms.Form):
    Email = forms.EmailField()
    Mobile = forms.IntegerField()
    Address = forms.CharField(max_length=500)




# for updating status of order
class OrderForm(forms.ModelForm):
    class Meta:
        model = models.Orders
        fields = ["status"]



    