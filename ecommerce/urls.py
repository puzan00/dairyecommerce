from django.contrib import admin
from django.urls import path
from ecom import views
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin Panel
    path("admin/", admin.site.urls),

    # General Views
    path("", views.home_view, name="home"),
    path("contactus/", views.contactus_view, name="contactus"),
    path("afterlogin/", views.afterlogin_view, name="afterlogin"),
    path("logout/", views.logout_view, name="logout"),

    # Admin Authentication
    path("adminclick/", views.adminclick_view),
    path("adminlogin/", LoginView.as_view(template_name="ecom/adminlogin.html"), name="adminlogin"),

    # Admin Dashboard & Management
    path("admin-dashboard/", views.admin_dashboard_view, name="admin-dashboard"),
    path("view-customer/", views.view_customer_view, name="view-customer"),

    # Product Management (Admin)
    path("admin-products/", views.admin_products_view, name="admin-products"),
    path("admin-add-product/", views.admin_add_product_view, name="admin-add-product"),
    path("update-product/<int:pk>/", views.update_product_view, name="update-product"),
    path("delete-product/<int:pk>/", views.delete_product_view, name="delete-product"),

    # Product Production Management (Admin)
    path("product-production-list/", views.product_production_list_view, name="product-production-list"),
    path("add-product-production/", views.add_product_production_view, name="add-product-production"),
    path("production/edit/<int:production_id>/", views.edit_product_production_view, name="edit-production"),
    path("production/delete/<int:production_id>/", views.delete_product_production_view, name="delete-production"),

    # Order Management
    path("admin-view-booking/", views.admin_view_booking_view, name="admin-view-booking"),
    path("delete-order/<int:pk>/", views.delete_order_view, name="delete-order"),
    path("update-order/<int:pk>/", views.update_order_view, name="update-order"),

    # Customer Authentication & Profile
    path("customersignup/", views.customer_signup_view),
    path("customerlogin/", LoginView.as_view(template_name="ecom/customerlogin.html"), name="customerlogin"),
    path("customer-home/", views.customer_home_view, name="customer-home"),
    path("my-profile/", views.my_profile_view, name="my-profile"),
    path("edit-profile/", views.edit_profile_view, name="edit-profile"),

    # Orders & Invoices
    path("my-order/", views.my_order_view, name="my-order"),
    path("download-invoice/<int:orderID>/<int:productID>/", views.download_invoice_view, name="download-invoice"),

    # Shopping Cart
    path("cart/", views.cart_view, name="cart"),
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add-to-cart"),
    path("remove-from-cart/<int:pk>/", views.remove_from_cart_view, name="remove-from-cart"),

    # Checkout & Payment
    path("customer-address/", views.customer_address_view, name="customer-address"),
    path("payment-success/", views.payment_success_view, name="payment-success"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
