from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


# Create your models here.
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(
        upload_to="profile_pic/CustomerProfilePic/", null=True, blank=True
    )
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20, null=False)

    @property
    def get_name(self):
        return self.user.first_name + " " + self.user.last_name

    @property
    def get_id(self):
        return self.user.id

    def __str__(self):
        return self.user.first_name


class Product(models.Model):
    name = models.CharField(max_length=40)
    product_image = models.ImageField(upload_to="product_image/", null=True, blank=True)
    price = models.PositiveIntegerField()
    description = models.CharField(max_length=100)  # Allow longer descriptions
    quantity = models.FloatField(default=0.0)  # For stock levels
    unit = models.CharField(max_length=20, default="kg")  # E.g., 'kg', 'liters'
    expiry_date = models.DateField(null=True, blank=True)  # Expiry tracking

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit} )"


class Orders(models.Model):
    STATUS = (
        ("Pending", "Pending"),
        ("Order Confirmed", "Order Confirmed"),
        ("Out for Delivery", "Out for Delivery"),
        ("Delivered", "Delivered"),
    )
    customer = models.ForeignKey("Customer", on_delete=models.CASCADE, null=True)
    product = models.ForeignKey("Product", on_delete=models.CASCADE, null=True)
    email = models.CharField(max_length=50, null=True)
    address = models.CharField(max_length=500, null=True)
    mobile = models.CharField(max_length=20, null=True)
    order_date = models.DateField(auto_now_add=True, null=True)
    status = models.CharField(max_length=50, null=True, choices=STATUS)


