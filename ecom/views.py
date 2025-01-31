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
    if "product_ids" in request.COOKIES:
        product_ids = request.COOKIES["product_ids"]
        counter = product_ids.split("|")
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0
    if request.user.is_authenticated:
        return HttpResponseRedirect("afterlogin")
    return render(
        request,
        "ecom/index.html",
        {"products": products, "product_count_in_cart": product_count_in_cart},
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
@login_required(login_url="adminlogin")
def delete_customer_view(request, pk):
    customer = models.Customer.objects.get(id=pk)
    user = models.User.objects.get(id=customer.user_id)
    user.delete()
    customer.delete()
    return redirect("view-customer")


@login_required(login_url="adminlogin")
def update_customer_view(request, pk):
    customer = models.Customer.objects.get(id=pk)
    user = models.User.objects.get(id=customer.user_id)
    userForm = forms.CustomerUserForm(instance=user)
    customerForm = forms.CustomerForm(request.FILES, instance=customer)
    mydict = {"userForm": userForm, "customerForm": customerForm}
    
    if request.method == "POST":
        userForm = forms.CustomerUserForm(request.POST, instance=user)
        customerForm = forms.CustomerForm(request.POST, instance=customer)
        
        if userForm.is_valid() and customerForm.is_valid():
            user = userForm.save(commit=False)  # Don't save user yet
            if userForm.cleaned_data.get('password'):
                user.set_password(userForm.cleaned_data['password'])  # Set new password only if provided
            user.save()  # Save the user object
            customerForm.save()  # Save the customer form
            return redirect("view-customer")
    
    return render(request, "ecom/admin_update_customer.html", context=mydict)

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
# ---------------------------------------------------------------------------------
def search_view(request):
    # whatever user write in search box we get in query
    query = request.GET["query"]
    products = models.Product.objects.all().filter(name__icontains=query)
    if "product_ids" in request.COOKIES:
        product_ids = request.COOKIES["product_ids"]
        counter = product_ids.split("|")
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0

    # word variable will be shown in html when user click on search button
    word = "Searched Result :"

    if request.user.is_authenticated:
        return render(
            request,
            "ecom/customer_home.html",
            {
                "products": products,
                "word": word,
                "product_count_in_cart": product_count_in_cart,
            },
        )
    return render(
        request,
        "ecom/index.html",
        {
            "products": products,
            "word": word,
            "product_count_in_cart": product_count_in_cart,
        },
    )


# any one can add product to cart, no need of signin

def add_to_cart_view(request, pk):
    """
    Adds a product to the cart. If the user is not authenticated, they are redirected to the login page.
    Ensures no duplicate product IDs are stored in cookies.
    """

    # Check if user is authenticated, otherwise redirect to login page
    if not request.user.is_authenticated:
        return redirect("customerlogin")

    # Retrieve existing product IDs from cookies
    product_ids = request.COOKIES.get("product_ids", "")
    product_id_list = product_ids.split("|") if product_ids else []

    # Avoid adding duplicates
    if str(pk) not in product_id_list:
        product_id_list.append(str(pk))

    # Prepare response with redirection to customer home
    response = redirect("customer-home")

    # Update cookies with new cart data
    response.set_cookie("product_ids", "|".join(product_id_list))

    return response
# for checkout of cart
def cart_view(request):
    # for cart counter
    if "product_ids" in request.COOKIES:
        product_ids = request.COOKIES["product_ids"]
        counter = product_ids.split("|")
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0

    # fetching product details from db whose id is present in cookie
    products = None
    total = 0
    if "product_ids" in request.COOKIES:
        product_ids = request.COOKIES["product_ids"]
        if product_ids != "":
            product_id_in_cart = product_ids.split("|")
            products = models.Product.objects.all().filter(id__in=product_id_in_cart)

            # for total price shown in cart
            for p in products:
                total = total + p.price
    return render(
        request,
        "ecom/cart.html",
        {
            "products": products,
            "total": total,
            "product_count_in_cart": product_count_in_cart,
        },
    )


def remove_from_cart_view(request, pk):
    # for counter in cart
    if "product_ids" in request.COOKIES:
        product_ids = request.COOKIES["product_ids"]
        counter = product_ids.split("|")
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0

    # removing product id from cookie
    total = 0
    if "product_ids" in request.COOKIES:
        product_ids = request.COOKIES["product_ids"]
        product_id_in_cart = product_ids.split("|")
        product_id_in_cart = list(set(product_id_in_cart))
        product_id_in_cart.remove(str(pk))
        products = models.Product.objects.all().filter(id__in=product_id_in_cart)
        # for total price shown in cart after removing product
        for p in products:
            total = total + p.price

        #  for update coookie value after removing product id in cart
        value = ""
        for i in range(len(product_id_in_cart)):
            if i == 0:
                value = value + product_id_in_cart[0]
            else:
                value = value + "|" + product_id_in_cart[i]
        response = render(
            request,
            "ecom/cart.html",
            {
                "products": products,
                "total": total,
                "product_count_in_cart": product_count_in_cart,
            },
        )
        if value == "":
            response.delete_cookie("product_ids")
        response.set_cookie("product_ids", value)
        return response





# ---------------------------------------------------------------------------------
# ------------------------ CUSTOMER RELATED VIEWS START ------------------------------
# ---------------------------------------------------------------------------------
@login_required(login_url="customerlogin")
@user_passes_test(is_customer)
def customer_home_view(request):
    products = models.Product.objects.all()
    out_of_stock_products = []
    in_stock_products = []

    for product in products:
        if models.Orders.objects.filter(product=product).exists():
            out_of_stock_products.append(product)
        else:
            in_stock_products.append(product)

    product_count_in_cart = 0
    if "product_ids" in request.COOKIES:
        product_ids = request.COOKIES["product_ids"]
        product_count_in_cart = len(set(product_ids.split("|")))

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
    # this is for checking whether product is present in cart or not
    # if there is no product in cart we will not show address form
    product_in_cart = False
    if "product_ids" in request.COOKIES:
        product_ids = request.COOKIES["product_ids"]
        if product_ids != "":
            product_in_cart = True
    # for counter in cart
    if "product_ids" in request.COOKIES:
        product_ids = request.COOKIES["product_ids"]
        counter = product_ids.split("|")
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0

    addressForm = forms.AddressForm()
    if request.method == "POST":
        addressForm = forms.AddressForm(request.POST)
        if addressForm.is_valid():
            # here we are taking address, email, mobile at time of order placement
            # we are not taking it from customer account table because
            # these thing can be changes
            email = addressForm.cleaned_data["Email"]
            mobile = addressForm.cleaned_data["Mobile"]
            address = addressForm.cleaned_data["Address"]
            # for showing total price on payment page.....accessing id from cookies then fetching  price of product from db
            total = 0
            if "product_ids" in request.COOKIES:
                product_ids = request.COOKIES["product_ids"]
                if product_ids != "":
                    product_id_in_cart = product_ids.split("|")
                    products = models.Product.objects.all().filter(
                        id__in=product_id_in_cart
                    )
                    for p in products:
                        total = total + p.price

            response = render(request, "ecom/payment.html", {"total": total})
            response.set_cookie("email", email)
            response.set_cookie("mobile", mobile)
            response.set_cookie("address", address)
            return response
    return render(
        request,
        "ecom/customer_address.html",
        {
            "addressForm": addressForm,
            "product_in_cart": product_in_cart,
            "product_count_in_cart": product_count_in_cart,
        },
    )


# here we are just directing to this view...actually we have to check whther payment is successful or not
# then only this view should be accessed
@login_required(login_url="customerlogin")
def payment_success_view(request):
    # Here we will place order | after successful payment
    # we will fetch customer  mobile, address, Email
    # we will fetch product id from cookies then respective details from db
    # then we will create order objects and store in db
    # after that we will delete cookies because after order placed...cart should be empty
    customer = models.Customer.objects.get(user_id=request.user.id)
    products = None
    email = None
    mobile = None
    address = None
    if "product_ids" in request.COOKIES:
        product_ids = request.COOKIES["product_ids"]
        if product_ids != "":
            product_id_in_cart = product_ids.split("|")
            products = models.Product.objects.all().filter(id__in=product_id_in_cart)
            # Here we get products list that will be ordered by one customer at a time

    # these things can be change so accessing at the time of order...
    if "email" in request.COOKIES:
        email = request.COOKIES["email"]
    if "mobile" in request.COOKIES:
        mobile = request.COOKIES["mobile"]
    if "address" in request.COOKIES:
        address = request.COOKIES["address"]

    # here we are placing number of orders as much there is a products
    # suppose if we have 5 items in cart and we place order....so 5 rows will be created in orders table
    # there will be lot of redundant data in orders table...but its become more complicated if we normalize it
    for product in products:
        models.Orders.objects.get_or_create(
            customer=customer,
            product=product,
            status="Pending",
            email=email, 
            mobile=mobile,
            address=address,
        )

    # after order placed cookies should be deleted
    response = render(request, "ecom/payment_success.html")
    response.delete_cookie("product_ids")
    response.delete_cookie("email")
    response.delete_cookie("mobile")
    response.delete_cookie("address")
    return response


@login_required(login_url="customerlogin")
@user_passes_test(is_customer)
def my_order_view(request):

    customer = models.Customer.objects.get(user_id=request.user.id)
    orders = models.Orders.objects.all().filter(customer_id=customer)
    ordered_products = []
    for order in orders:
        ordered_product = models.Product.objects.all().filter(id=order.product.id)
        ordered_products.append(ordered_product)

    return render(
        request, "ecom/my_order.html", {"data": zip(ordered_products, orders)}
    )


# @login_required(login_url='customerlogin')
# @user_passes_test(is_customer)
# def my_order_view2(request):

#     products=models.Product.objects.all()
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         counter=product_ids.split('|')
#         product_count_in_cart=len(set(counter))
#     else:
#         product_count_in_cart=0
#     return render(request,'ecom/my_order.html',{'products':products,'product_count_in_cart':product_count_in_cart})


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
    customer = models.Customer.objects.get(user_id=request.user.id)
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
def aboutus_view(request):
    return render(request, "ecom/aboutus.html")


def contactus_view(request):
    return render(request, "ecom/contactus.html")
