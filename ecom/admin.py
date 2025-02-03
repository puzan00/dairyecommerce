from django.contrib import admin
from .models import Customer,Product,Orders,Cart
# Register your models here.
class CustomerAdmin(admin.ModelAdmin):
    pass
admin.site.register(Customer, CustomerAdmin)

class ProductAdmin(admin.ModelAdmin):
    pass
admin.site.register(Product, ProductAdmin)

class OrderAdmin(admin.ModelAdmin):
    pass
admin.site.register(Orders, OrderAdmin)

class CartAdmin(admin.ModelAdmin):
    list_display = ("customer", "product")

admin.site.register(Cart, CartAdmin)
