from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils.timezone import now

# Create your models here.
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(
        upload_to="profile_pic/", null=True, blank=True
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
    description = models.CharField(max_length=100)  # Description field
    quantity = models.FloatField(default=0.0)  # For stock levels
    unit = models.CharField(max_length=20, default="kg")  # E.g., 'kg', 'liters'
    expiry_date = models.DateField(null=True, blank=True)  # Expiry tracking
    date_added = models.DateField(default=now)  # Add this field
    is_sold = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"
    

from django.db import models

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
    quantity = models.PositiveIntegerField(default=1)  # Ensure this line is present

    def __str__(self):
        return f"Order {self.id} by {self.customer.get_name} for {self.product.name} (Quantity: {self.quantity})"

class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)  # Add this line

    class Meta:
        unique_together = ('customer', 'product')

class ProductProduction(models.Model):
    product_name = models.CharField(max_length=100, null=True, blank=True)
    product_unit = models.CharField(max_length=20, null=True, blank=True) 
    quantity_produced = models.FloatField()        
    production_date = models.DateField(default=now) 

    def __str__(self):
        return f"{self.quantity_produced} {self.product_unit} of {self.product_name} produced on {self.production_date}"