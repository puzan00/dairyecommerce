from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from . import models


class CustomerUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "password"]


class CustomerForm(forms.ModelForm):
    class Meta:
        model = models.Customer
        fields = ["address", "mobile", "profile_pic"]


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


class AddressForm(forms.Form):
    Email = forms.EmailField()
    Mobile = forms.IntegerField()
    Address = forms.CharField(max_length=500)


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = models.Feedback
        fields = ["name", "feedback"]


class OrderForm(forms.ModelForm):
    class Meta:
        model = models.Orders
        fields = ["status"]


class ContactusForm(forms.Form):
    Name = forms.CharField(max_length=30)
    Email = forms.EmailField()
    Message = forms.CharField(
        max_length=500, widget=forms.Textarea(attrs={"rows": 3, "cols": 30})
    )
