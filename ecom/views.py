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
from .models import Cart, Product, Customer,ProductProduction,Orders
from django.db import transaction


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

from collections import defaultdict
from django.db.models import Sum, F

from .models import Orders, Customer, Product, ProductProduction
from django.db.models.functions import TruncWeek


from collections import defaultdict
from datetime import date, timedelta

def admin_dashboard_view(request):
    # Counts for dashboard cards
    orders = Orders.objects.all().order_by('-order_date')
    ordered_products = []
    ordered_bys = []
    product_quantities = []
    product_units = []

    for order in orders:
        ordered_product = order.product
        ordered_by = order.customer
        ordered_products.append(ordered_product)
        ordered_bys.append(ordered_by)
        product_quantities.append(order.quantity)  # Quantity from the order
        product_units.append(ordered_product.unit)  # Unit from the product

    data = zip(ordered_products, ordered_bys, orders, product_quantities, product_units)

    customer_count = Customer.objects.count()
    product_count = Product.objects.count()
    order_count = Orders.objects.count()

    # Recent Orders Data
    recent_orders = Orders.objects.select_related("customer", "product").order_by("-order_date")[:10]

    # Expiry Alerts
    today = date.today()
    expired_products = Product.objects.filter(expiry_date__lt=today)
    expiry_7_days = Product.objects.filter(expiry_date__range=[today, today + timedelta(days=7)])
    expiry_30_days = Product.objects.filter(expiry_date__range=[today + timedelta(days=8), today + timedelta(days=30)])

    # Orders Status Distribution
    order_status_count = {
        "Pending": Orders.objects.filter(status="Pending").count(),
        "OrderConfirmed": Orders.objects.filter(status="Order Confirmed").count(),
        "OutforDelivery": Orders.objects.filter(status="Out for Delivery").count(),
        "Delivered": Orders.objects.filter(status="Delivered").count(),
    }

    # Product production data for the chart
    product_productions = ProductProduction.objects.all()

    # Group production data by date first, then product name
    production_data = defaultdict(list)

    for production in product_productions:
        production_data[production.production_date].append({
            'product_name': production.product.name,
            'quantity_produced': production.quantity_produced,
        })

    # Prepare data for the chart, sorting by production_date in ascending order
    production_labels = []
    production_quantities = []
    production_dates = []

    # Sort by production date (ascending order)
    sorted_production_dates = sorted(production_data.keys())

    for production_date in sorted_production_dates:
        for entry in production_data[production_date]:
            production_labels.append(f"{entry['product_name']} ({production_date.strftime('%m-%d')})")

            production_quantities.append(entry['quantity_produced'])
            production_dates.append(production_date)

    # Sales Data - Total Sales (for total sales analysis)
    total_sales = Orders.objects.aggregate(
        total_sales=Sum(F('product__price') * F('quantity'))
    )['total_sales'] or 0

    # Highest Sales (highest sales in a single order)
    highest_sales_order = Orders.objects.annotate(
        order_sales=F('product__price') * F('quantity')
    ).order_by('-order_sales').first()

    highest_sales = highest_sales_order.order_sales if highest_sales_order else 0
    highest_sales_product = highest_sales_order.product.name if highest_sales_order else 'N/A'
    highest_sales_quantity = highest_sales_order.product.quantity if highest_sales_order else 0
    highest_sales_unit = highest_sales_order.product.unit if highest_sales_order else 'N/A'

    # Lowest Sales (lowest sales in a single order)
    lowest_sales_order = Orders.objects.annotate(
        order_sales=F('product__price') * F('quantity')
    ).order_by('order_sales').first()

    lowest_sales = lowest_sales_order.order_sales if lowest_sales_order else 0
    lowest_sales_product = lowest_sales_order.product.name if lowest_sales_order else 'N/A'
    lowest_sales_quantity = lowest_sales_order.product.quantity if lowest_sales_order else 0
    lowest_sales_unit = lowest_sales_order.product.unit if lowest_sales_order else 'N/A'

    # Total Orders (Count of all orders)
    total_orders = Orders.objects.count()

    # Context for rendering the dashboard
    context = {
        "data": data,
        "customercount": customer_count,
        "productcount": product_count,
        "ordercount": order_count,
        "total_sales": total_sales,
        "total_orders": total_orders,
        "highest_sales": highest_sales,
        "highest_sales_product": highest_sales_product,
        "highest_sales_quantity": highest_sales_quantity,
        "highest_sales_unit": highest_sales_unit,
        "lowest_sales": lowest_sales,
        "lowest_sales_product": lowest_sales_product,
        "lowest_sales_quantity": lowest_sales_quantity,
        "lowest_sales_unit": lowest_sales_unit,
        "recent_orders": recent_orders,
        "expired_products": expired_products,
        "expiry_7_days": expiry_7_days,
        "expiry_30_days": expiry_30_days,
        "order_status_count": order_status_count,
        "production_labels": production_labels,
        "production_quantities": production_quantities,
        "production_dates": production_dates,
    }

    return render(request, "ecom/admin_dashboard.html", context)




def add_product_production_view(request):
    # Get the list of products
    products = Product.objects.all()

    if request.method == 'POST':
        # Handle form submission
        product_id = request.POST.get('product')
        quantity_produced = request.POST.get('quantity_produced')
        production_date = request.POST.get('production_date')
        
        # Get the selected product by id
        selected_product = Product.objects.get(id=product_id)
        
        # Create a new ProductProduction instance
        new_production = ProductProduction(
            product=selected_product,
            quantity_produced=quantity_produced,
            production_date=production_date
        )
        
        # Save the new production record
        new_production.save()
        
        # After saving, redirect to the product production list page
        return redirect('product-production-list')  # This uses the URL name defined in urls.py

    # Render the form if it's a GET request
    context = {'products': products}
    return render(request, 'ecom/add_product_production.html', context)

def edit_product_production_view(request, production_id):
    production = ProductProduction.objects.get(id=production_id)
    products = Product.objects.all()

    if request.method == 'POST':
        production.product_id = request.POST.get('product')
        production.quantity_produced = request.POST.get('quantity_produced')
        production.production_date = request.POST.get('production_date')
        production.save()
        return redirect('product-production-list')

    context = {
        'production': production,
        'products': products,
    }
    return render(request, 'ecom/edit_product_production.html', context)

def delete_product_production_view(request, production_id):
    production = get_object_or_404(ProductProduction, id=production_id)

    if request.method == 'POST':
        production.delete()
        return redirect('product-production-list')  # Redirect to the same page to refresh the list

    # If method is not POST, render confirmation or the list page directly
    return redirect('product-production-list')

from datetime import date

def product_production_list_view(request):
    # Get all product production records
    product_productions = ProductProduction.objects.all()

    # Calculate total quantity produced for each product by date
    product_totals = {}
    for production in product_productions:
        product = production.product
        production_date = production.production_date  # Use the date as is
        quantity_produced = production.quantity_produced

        # Initialize the product entry in the product_totals if not already present
        if product not in product_totals:
            product_totals[product] = {'total_quantity': 0, 'dates': {}}
        
        # Add the quantity to the total for that product
        product_totals[product]['total_quantity'] += quantity_produced

        # Add the quantity for a specific date if needed
        if production_date not in product_totals[product]['dates']:
            product_totals[product]['dates'][production_date] = 0
        product_totals[product]['dates'][production_date] += quantity_produced

    # Pass product_totals to the template
    return render(request, "ecom/product_production_list.html", {
        'product_productions': product_productions,
        'product_totals': product_totals,
    })



# admin view customer table
@login_required(login_url="adminlogin")
def view_customer_view(request):
    customers = models.Customer.objects.all()
    return render(request, "ecom/view_customer.html", {"customers": customers})




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
    orders = models.Orders.objects.all().order_by('-order_date')
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



def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect("customerlogin")

    product = get_object_or_404(Product, id=product_id)
    customer = get_object_or_404(Customer, user=request.user)

    # Check if the product is already in the cart of any customer
    existing_cart_item = Cart.objects.filter(product=product).first()

    if existing_cart_item:
        # If the product is already in another cart, it's out of stock for the current user
        messages.error(request, f"{product.name} is already in another cart and is out of stock!")
        return redirect("customer-home")
    
    # Add product to cart (1 quantity)
    Cart.objects.create(customer=customer, product=product, quantity=1)
    
    # Now the product is effectively out of stock for others, no need to track its quantity in the model.
    messages.success(request, f"{product.name} has been added to your cart.")

    return redirect("cart")


# In views.py

# Updated cart view with stock validation
def cart_view(request):
    if not request.user.is_authenticated:
        return redirect("customerlogin")

    customer = get_object_or_404(Customer, user=request.user)
    cart_items = Cart.objects.filter(customer=customer).select_related('product')
    
    # Validate stock levels for each cart item
    for item in cart_items:
        if item.quantity > item.product.quantity:
            item.quantity = item.product.quantity
            item.save()
            if item.product.quantity == 0:
                item.delete()
                messages.warning(request, f"{item.product.name} has been removed from cart (Out of Stock)")
            else:
                messages.warning(request, f"Quantity adjusted for {item.product.name} due to stock availability")

    # Recalculate total after any adjustments
    total = sum(item.product.price * item.quantity for item in cart_items)
    product_count_in_cart = cart_items.count()

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
from django.utils import timezone

@login_required(login_url="customerlogin")
@user_passes_test(is_customer)
def customer_home_view(request):
    # Get all products
    products = Product.objects.all()

    # Get current date to compare expiry date
    today = timezone.now().date()

    # Identify out-of-stock products based on order statuses
    out_of_stock_products = products.filter(
        orders__status__in=["Pending", "Order Confirmed", "Out for Delivery", "Delivered"]
    ).distinct()

    # Filter expired products
    expired_products = products.filter(expiry_date__lt=today)

    # Products that are still in stock and not expired
    in_stock_products = products.exclude(id__in=out_of_stock_products).exclude(id__in=expired_products)

    # Fetch the current customer's cart items
    customer = get_object_or_404(Customer, user=request.user)
    cart_items = Cart.objects.filter(customer=customer)

    # Count the number of items in the cart
    product_count_in_cart = cart_items.count()

    return render(
        request,
        "ecom/customer_home.html",
        {
            "in_stock_products": in_stock_products,
            "out_of_stock_products": out_of_stock_products,
            "product_count_in_cart": product_count_in_cart,
        }
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


# Updated payment success view with better stock management
@login_required(login_url="customerlogin")
def payment_success_view(request):
    customer = get_object_or_404(models.Customer, user=request.user)
    cart_items = models.Cart.objects.filter(customer=customer).select_related('product')

    order_details = request.session.get('order_details')
    if not order_details:
        return redirect('customer_address')

    with transaction.atomic():
        # First, verify stock availability for all items
        for cart_item in cart_items:
            if cart_item.quantity > cart_item.product.quantity:
                return render(request, "ecom/payment_failed.html", 
                    {"message": f"Insufficient stock for {cart_item.product.name}"})

        orders = []
        # If all stock checks pass, create orders and update stock
        for cart_item in cart_items:
            # Create order
            order = models.Orders(
                customer=customer,
                product=cart_item.product,
                status="Pending",
                email=order_details.get('email', ''),
                mobile=order_details.get('mobile', ''),
                address=order_details.get('address', ''),
                quantity=cart_item.quantity
            )
            orders.append(order)

            # Update product stock
            cart_item.product.quantity -= cart_item.quantity
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
