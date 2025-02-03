from django.shortcuts import render, redirect, reverse
from . import forms, models
from django.http import HttpResponseRedirect, HttpResponse
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib.auth import logout
from .models import Cart, Product, Customer


def increase_quantity(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.quantity += 1
    product.save()
    return redirect("cart")


def decrease_quantity(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.quantity > 1:  # Prevent reducing quantity below 1
        product.quantity -= 1
        product.save()
    return redirect("cart")


def home_view(request):
    products = models.Product.objects.all()

    # Remove the logic for counting products in cart
    if request.user.is_authenticated:
        return HttpResponseRedirect("afterlogin")

    return render(
        request,
        "ecom/index.html",
        {"products": products},  # Remove product_count_in_cart from context
    )

# for showing login button for admin(by pujan)
def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("afterlogin")
    return HttpResponseRedirect("adminlogin")
def customer_signup_view(request):
    # Instantiate the forms
    userForm = forms.CustomerUserForm()
    customerForm = forms.CustomerForm()
    context = {"userForm": userForm, "customerForm": customerForm}

    # Check if the request is POST (form submission)
    if request.method == "POST":
        userForm = forms.CustomerUserForm(request.POST)
        customerForm = forms.CustomerForm(request.POST, request.FILES)

        if userForm.is_valid() and customerForm.is_valid():
            username = userForm.cleaned_data.get('username')
            email = userForm.cleaned_data.get('email')

            # Check if username or email already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
           
            else:
                # Save the user data and set password (from the form input)
                user = userForm.save()
                user.set_password(user.password)  # Ensure the password is hashed
                user.save()

                # Save the customer data without committing (so we can assign the user)
                customer = customerForm.save(commit=False)
                customer.user = user  # Link the user to the customer profile
                customer.save()

                # Add user to the "CUSTOMER" group
                my_customer_group = Group.objects.get_or_create(name="CUSTOMER")
                my_customer_group[0].user_set.add(user)

                # Add success message
                messages.success(request, "Account created successfully!")
                return redirect('customerlogin')  # Use the 'redirect' method with the named URL

    # Render the signup page with form data
    return render(request, "ecom/customersignup.html", context)


# -----------for checking user iscustomer
def is_customer(user):
    return user.groups.filter(name="CUSTOMER").exists()


# ---------AFTER ENTERING CREDENTIALS WE CHECK WHETHER USERNAME AND PASSWORD IS OF ADMIN,CUSTOMER
def afterlogin_view(request):
    if is_customer(request.user):
        return redirect("customer-home")
    else:
        return redirect("admin-dashboard")

def logout_view(request):
    logout(request)
    return redirect('customerlogin')
# ---------------------------------------------------------------------------------
# ------------------------ ADMIN RELATED VIEWS START ------------------------------
# ---------------------------------------------------------------------------------

from django.shortcuts import render
from datetime import timedelta, date
from .models import Customer, Product, Orders

from datetime import date, timedelta
from django.shortcuts import render


def admin_dashboard_view(request):
    # Counts for dashboard cards
    orders = Orders.objects.all()
    ordered_products = []
    ordered_bys = []
    for order in orders:
        ordered_product = order.product
        ordered_by = order.customer
        ordered_products.append(ordered_product)
        ordered_bys.append(ordered_by)

    data = zip(ordered_products, ordered_bys, orders)

    customer_count = Customer.objects.count()
    product_count = Product.objects.count()
    order_count = Orders.objects.count()

    # Recent Orders Data
    recent_orders = Orders.objects.select_related("customer", "product").order_by(
        "-order_date"
    )[:10]

    # Expiry Alerts
    today = date.today()
    expired_products = Product.objects.filter(expiry_date__lt=today)
    expiry_7_days = Product.objects.filter(
        expiry_date__range=[today, today + timedelta(days=7)]
    )
    expiry_30_days = Product.objects.filter(
        expiry_date__range=[today + timedelta(days=8), today + timedelta(days=30)]
    )

    # Inventory Monitoring
    low_stock_products = Product.objects.filter(
        quantity__lt=10
    )  # Example threshold for low stock
    high_stock_products = Product.objects.filter(quantity__gte=10)

    # Orders Status Distribution
    order_status_count = {
        "Pending": Orders.objects.filter(status="Pending").count(),
        "OrderConfirmed": Orders.objects.filter(status="Order Confirmed").count(),
        "OutforDelivery": Orders.objects.filter(status="Out for Delivery").count(),
        "Delivered": Orders.objects.filter(status="Delivered").count(),
    }

    context = {
        "data": data,
        "customercount": customer_count,
        "productcount": product_count,
        "ordercount": order_count,
        "recent_orders": recent_orders,
        "expired_products": expired_products,
        "expiry_7_days": expiry_7_days,
        "expiry_30_days": expiry_30_days,
        "low_stock_products": low_stock_products,
        "high_stock_products": high_stock_products,
        "order_status_count": order_status_count,
    }

    return render(request, "ecom/admin_dashboard.html", context)


# admin view customer table
@login_required(login_url="adminlogin")
def view_customer_view(request):
    customers = models.Customer.objects.all()
    return render(request, "ecom/view_customer.html", {"customers": customers})


# admin delete customer
# @login_required(login_url="adminlogin")
# def delete_customer_view(request, pk):
#     customer = models.Customer.objects.get(id=pk)
#     user = models.User.objects.get(id=customer.user_id)
#     user.delete()
#     customer.delete()
#     return redirect("view-customer")


# @login_required(login_url="adminlogin")
# def update_customer_view(request, pk):
#     customer = models.Customer.objects.get(id=pk)
#     user = models.User.objects.get(id=customer.user_id)
#     userForm = forms.CustomerUserForm(instance=user)
#     customerForm = forms.CustomerForm(request.FILES, instance=customer)
#     mydict = {"userForm": userForm, "customerForm": customerForm}
    
#     if request.method == "POST":
#         userForm = forms.CustomerUserForm(request.POST, instance=user)
#         customerForm = forms.CustomerForm(request.POST, instance=customer)
        
#         if userForm.is_valid() and customerForm.is_valid():
#             user = userForm.save(commit=False)  # Don't save user yet
#             if userForm.cleaned_data.get('password'):
#                 user.set_password(userForm.cleaned_data['password'])  # Set new password only if provided
#             user.save()  # Save the user object
#             customerForm.save()  # Save the customer form
#             return redirect("view-customer")
    
#     return render(request, "ecom/admin_update_customer.html", context=mydict)

# admin view the product
@login_required(login_url="adminlogin")
def admin_products_view(request):
    products = models.Product.objects.all()
    return render(request, "ecom/admin_products.html", {"products": products})


# admin add product by clicking on floating button
@login_required(login_url="adminlogin")
def admin_add_product_view(request):
    productForm = forms.ProductForm()
    if request.method == "POST":
        productForm = forms.ProductForm(request.POST, request.FILES)
        if productForm.is_valid():
            productForm.save()
        return HttpResponseRedirect("admin-products")
    return render(request, "ecom/admin_add_products.html", {"productForm": productForm})


from datetime import date


def check_inventory_and_expiry():
    products = Product.objects.all()
    low_stock_alerts = []
    expiry_alerts = []
    for product in products:
        if product.quantity < 10:  # Threshold for low stock
            low_stock_alerts.append(f"{product.name} is low on stock!")
        if product.expiry_date and (product.expiry_date - date.today()).days <= 7:
            expiry_alerts.append(f"{product.name} is nearing expiry!")
    return low_stock_alerts, expiry_alerts


@login_required(login_url="adminlogin")
def delete_product_view(request, pk):
    product = models.Product.objects.get(id=pk)
    product.delete()
    return redirect("admin-products")


@login_required(login_url="adminlogin")
def update_product_view(request, pk):
    product = models.Product.objects.get(id=pk)
    productForm = forms.ProductForm(instance=product)

    if request.method == "POST":
        productForm = forms.ProductForm(request.POST, request.FILES, instance=product)
        if productForm.is_valid():
            productForm.save()
            return redirect("admin-products")
        else:
            pass
    return render(
        request, "ecom/admin_update_product.html", {"productForm": productForm}
    )


@login_required(login_url="adminlogin")
def admin_view_booking_view(request):
    orders = models.Orders.objects.all()
    ordered_products = []
    ordered_bys = []
    for order in orders:
        ordered_product = models.Product.objects.all().filter(id=order.product.id)
        ordered_by = models.Customer.objects.all().filter(id=order.customer.id)
        ordered_products.append(ordered_product)
        ordered_bys.append(ordered_by)
    return render(
        request,
        "ecom/admin_view_booking.html",
        {"data": zip(ordered_products, ordered_bys, orders)},
    )


@login_required(login_url="adminlogin")
def delete_order_view(request, pk):
    order = models.Orders.objects.get(id=pk)
    order.delete()
    return redirect("admin-view-booking")


# for changing status of order (pending,delivered...)
@login_required(login_url="adminlogin")
def update_order_view(request, pk):
    order = models.Orders.objects.get(id=pk)
    orderForm = forms.OrderForm(instance=order)
    if request.method == "POST":
        orderForm = forms.OrderForm(request.POST, instance=order)
        if orderForm.is_valid():
            orderForm.save()
            return redirect("admin-view-booking")
    return render(request, "ecom/update_order.html", {"orderForm": orderForm})





# ---------------------------------------------------------------------------------
# ------------------------ PUBLIC CUSTOMER RELATED VIEWS START ---------------------
# ---------------------------------------------------------------------------------from django.shortcuts import redirect, get_object_or_404, render


# Add product to cart
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect("customerlogin")  # Redirect to login page if not authenticated

    # Get the product the customer is adding to the cart
    product = get_object_or_404(Product, id=product_id)

    # Get the current customer (the logged-in user)
    customer = get_object_or_404(Customer, user=request.user)

    # Check if the product is already in the cart for the customer
    cart_item, created = Cart.objects.get_or_create(
        customer=customer, product=product
    )


    # Redirect to the cart view after adding the product
    return redirect("cart")
# View the cart
# In views.py


def cart_view(request):
    if not request.user.is_authenticated:
        return redirect("customerlogin")  # Redirect to login page if not authenticated

    # Get the current customer (the logged-in user)
    customer = get_object_or_404(Customer, user=request.user)

    # Get all cart items for the customer
    cart_items = Cart.objects.filter(customer=customer)

    # Calculate the total amount (no quantity adjustments, just sum the price of each product)
    total = sum(item.product.price for item in cart_items)

    # Get the count of items in the cart
    product_count_in_cart = cart_items.count()

    # Render the cart page with the context
    return render(request, "ecom/cart.html", {
        "cart_items": cart_items,
        "total": total,
        "product_count_in_cart": product_count_in_cart,
    })

def remove_from_cart_view(request, pk):
    if not request.user.is_authenticated:
        return redirect("customerlogin")  # Redirect to login page if not authenticated

    # Get the cart item to be removed
    cart_item = get_object_or_404(Cart, id=pk)  # Use 'pk' here, not 'cart_item_id'

    # Ensure that the cart item belongs to the logged-in user
    if cart_item.customer.user != request.user:
        return redirect("cart")  # Prevent unauthorized removal

    # Delete the cart item
    cart_item.delete()

    # Redirect to the cart view after removal
    return redirect("cart")




# ---------------------------------------------------------------------------------
# ------------------------ CUSTOMER RELATED VIEWS START ------------------------------
# ---------------------------------------------------------------------------------
@login_required(login_url="customerlogin")
@user_passes_test(is_customer)
def customer_home_view(request):
    products = models.Product.objects.all()
    # Modify the stock check logic to use the quantity field
    out_of_stock_products = products.filter(quantity=0)
    in_stock_products = products.exclude(quantity=0)
    
    # Get cart count directly from the database
    product_count_in_cart = models.Cart.objects.filter(customer__user=request.user).count()
    
    return render(
        request,
        "ecom/customer_home.html",
        {
            "in_stock_products": in_stock_products,
            "out_of_stock_products": out_of_stock_products,
            "product_count_in_cart": product_count_in_cart,
        },
    )

# shipment address before placing order


@login_required(login_url="customerlogin")
def customer_address_view(request):
    customer = get_object_or_404(models.Customer, user=request.user)
    cart_items = models.Cart.objects.filter(customer=customer)
    
    if not cart_items.exists():
        return redirect("cart")
    
    # Calculate total here to pass to both POST and GET renders
    total = sum(item.product.price for item in cart_items)
    
    if request.method == "POST":
        address_form = forms.AddressForm(request.POST)
        if address_form.is_valid():
            # Store address details in session instead of cookies
            request.session['order_details'] = {
                'email': address_form.cleaned_data["Email"],
                'mobile': address_form.cleaned_data["Mobile"],
                'address': address_form.cleaned_data["Address"],
            }
            return render(request, "ecom/payment.html", {"total": total})
    else:
        # Pre-fill form with existing customer data
        address_form = forms.AddressForm(initial={
            'Email': customer.user.email,
            'Mobile': customer.mobile,
            'Address': customer.address,
        })
    
    return render(
        request,
        "ecom/customer_address.html",
        {
            "addressForm": address_form,
            "product_count_in_cart": cart_items.count(),
            "total": total,
        },
    )


# here we are just directing to this view...actually we have to check whther payment is successful or not
# then only this view should be accessed



from django.db import transaction  # Add this import

@login_required(login_url="customerlogin")
def payment_success_view(request):
    customer = get_object_or_404(models.Customer, user=request.user)
    cart_items = models.Cart.objects.filter(customer=customer)

    order_details = request.session.get('order_details', {})

    with transaction.atomic():
        orders = []
        for cart_item in cart_items:
            order_quantity = 1  # Assume 1 unit for now, adjust based on user input if needed
            # Create a new order
            order = models.Orders(
                customer=customer,
                product=cart_item.product,
                status="Pending",
                email=order_details.get('email', ''),
                mobile=order_details.get('mobile', ''),
                address=order_details.get('address', ''),
                quantity=order_quantity  # Store quantity in the order
            )
            orders.append(order)

            # Decrease the product stock based on quantity
            cart_item.product.quantity -= order_quantity
            cart_item.product.save()

        # Bulk create orders
        models.Orders.objects.bulk_create(orders)

        # Clear cart and session
        cart_items.delete()
        request.session.pop('order_details', None)

    return render(request, "ecom/payment_success.html", {"orders": orders})


@login_required(login_url="customerlogin")
@user_passes_test(is_customer)
def my_order_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    orders = models.Orders.objects.filter(customer=customer).select_related('product')  # Optimized query
    
    return render(
        request,
        "ecom/my_order.html",
        {"orders": orders}  # Pass the orders queryset directly to the template
    )





# --------------for discharge customer bill (pdf) download and printing
import io
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type="application/pdf")
    return


@login_required(login_url="customerlogin")
@user_passes_test(is_customer)
def download_invoice_view(request, orderID, productID):
    order = models.Orders.objects.get(id=orderID)
    product = models.Product.objects.get(id=productID)
    mydict = {
        "orderDate": order.order_date,
        "customerName": request.user,
        "customerEmail": order.email,
        "customerMobile": order.mobile,
        "shipmentAddress": order.address,
        "orderStatus": order.status,
        "productName": product.name,
        "productImage": product.product_image,
        "productPrice": product.price,
        "productDescription": product.description,
    }
    return render_to_pdf("ecom/download_invoice.html", mydict)


@login_required(login_url="customerlogin")
@user_passes_test(is_customer)
def my_profile_view(request):
    try:
        # Attempt to get the customer associated with the logged-in user
        customer = models.Customer.objects.get(user_id=request.user.id)
    except models.Customer.DoesNotExist:
        # If no customer is found, raise an error or redirect to another page
        raise Http404("Customer not found")

    # Return the profile page with the customer object
    return render(request, "ecom/my_profile.html", {"customer": customer})
@login_required(login_url='customerlogin')
def edit_profile_view(request):
    customer = get_object_or_404(models.Customer, user=request.user)
    user = request.user  # Directly use the authenticated user

    if request.method == "POST":
        # Use the new forms: EditProfileForm (without password) and EditCustomerForm
        userForm = forms.EditProfileForm(request.POST, instance=user)  # Without password field
        customerForm = forms.EditCustomerForm(request.POST, request.FILES, instance=customer)

        if userForm.is_valid() and customerForm.is_valid():
            userForm.save()  # Save user details (excluding password)
            customerForm.save()  # Save customer details

            # Log to verify the redirect URL
            next_url = request.GET.get('next', 'my-profile')  # Get 'next' or fallback to 'my-profile'
            print(f"Redirecting to: {next_url}")
            return redirect(next_url)  # Redirect to 'next' or fallback

    else:
        # Prefill the forms with the current user and customer data
        userForm = forms.EditProfileForm(instance=user)  # Without password field
        customerForm = forms.EditCustomerForm(instance=customer)

    return render(request, "ecom/edit_profile.html", {"userForm": userForm, "customerForm": customerForm})
# ---------------------------------------------------------------------------------
# ------------------------ ABOUT US AND CONTACT US VIEWS START --------------------
# ---------------------------------------------------------------------------------


def contactus_view(request):
    return render(request, "ecom/contactus.html")
