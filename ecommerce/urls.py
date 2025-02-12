from django.contrib import admin
from django.urls import path
from ecom import views
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.conf.urls.static import static
from ecom.views import admin_login_view 

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home_view, name="home"),
    path("afterlogin/", views.afterlogin_view, name="afterlogin"),
    path('logout/', views.logout_view, name='logout'),
    path("contactus/", views.contactus_view, name="contactus"),  # Added slash here
    
    path("adminlogin/", admin_login_view, name="adminlogin"),
    path("product-production-list/", views.product_production_list_view, name="product-production-list"),  # Added slash
    path("add-product-production/", views.add_product_production_view, name="add-product-production"),  # Added slash
    path('production/edit/<int:production_id>/', views.edit_product_production_view, name='edit-production'),
    path('production/delete/<int:production_id>/', views.delete_product_production_view, name='delete-production'),
    path("admin-dashboard/", views.admin_dashboard_view, name="admin-dashboard"),  # Added slash
    path("view-customer/", views.view_customer_view, name="view-customer"),  # Added slash
    
    path("admin-products/", views.admin_products_view, name="admin-products"),  # Added slash
    path("admin-add-product/", views.admin_add_product_view, name="admin-add-product"),  # Added slash
    path("delete-product/<int:pk>/", views.delete_product_view, name="delete-product"),  # Added slash
    path("update-product/<int:pk>/", views.update_product_view, name="update-product"),  # Added slash
    path(
        "admin-view-booking/", views.admin_view_booking_view, name="admin-view-booking"
    ),  # Added slash
    path("delete-order/<int:pk>/", views.delete_order_view, name="delete-order"),  # Added slash
    path("update-order/<int:pk>/", views.update_order_view, name="update-order"),  # Added slash
    path("customersignup/", views.customer_signup_view, name="customersignup"),  # Added slash
    path(
        "customerlogin/",  # Already with slash
        LoginView.as_view(template_name="ecom/customerlogin.html"),
        name="customerlogin",
    ),
    path("customer-home/", views.customer_home_view, name="customer-home"),  # Added slash
    path("my-order/", views.my_order_view, name="my-order"), 
    path("my-profile/", views.my_profile_view, name="my-profile"),  # Added slash
    path("edit-profile/", views.edit_profile_view, name="edit-profile"),  # Added slash
    path(
        "download-invoice/<int:orderID>/<int:productID>/",  # Added slash
        views.download_invoice_view,
        name="download-invoice",
    ),
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add-to-cart"),  # Added slash
    path("cart/", views.cart_view, name="cart"),  # Added slash
    path(
        "remove-from-cart/<int:pk>/",  # Added slash
        views.remove_from_cart_view,
        name="remove-from-cart",
    ),
    path("customer-address/", views.customer_address_view, name="customer-address"),  # Added slash
    path("payment-success/", views.payment_success_view, name="payment-success"),  # Added slash
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
