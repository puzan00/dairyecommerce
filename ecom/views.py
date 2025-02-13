from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Sum, F
from django.db.models.functions import TruncWeek
from datetime import date, timedelta
from collections import defaultdict
from .models import Cart, Product, Customer, ProductProduction, Orders
from django.conf import settings
from . import forms, models
from django.utils import timezone
import io
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import Context
from django.urls import reverse
from django.utils.timezone import now, timedelta
from django.contrib.auth.models import User, Group

# Home view: Displays the homepage with a list of products.
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

# Admin login view: Handles admin login and redirects based on authentication.
def admin_login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:  # Check if user is admin
                login(request, user)  
                return redirect("admin-dashboard")  # Redirect to admin dashboard
            else:
                messages.error(request, "Access denied. Admins only.")
                return redirect("adminlogin")  
    else:
        form = AuthenticationForm()

    return render(request, "ecom/adminlogin.html", {"form": form})

# Customer signup view: Handles customer signup and validation.
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

# After login: Redirect based on user type (Admin or Customer)
def afterlogin_view(request):
    if is_customer(request.user):
        return redirect("customer-home")
    else:
        return redirect("admin-dashboard")

# Logout view: Logs the user out and redirects to the login page.
def logout_view(request):
    logout(request)
    return redirect('customerlogin')

# ---------------------------------------------------------------------------------
# ------------------------ ADMIN RELATED VIEWS START ------------------------------
# ---------------------------------------------------------------------------------

@login_required(login_url="adminlogin")
def admin_dashboard_view(request):
    # Counts for dashboard cards
    orders = Orders.objects.select_related("customer", "product").order_by('-order_date')
    
    customer_count = Customer.objects.count()
    product_count = Product.objects.count()
    order_count = orders.count()

    # Recent Orders Data
    recent_orders = orders[:10]

  # Expiry Alert Data
    today = now().date()
    tomorrow = today + timedelta(days=1)
    three_days = today + timedelta(days=3)
    week_later = today + timedelta(days=7)
    thirty_days_later = today + timedelta(days=30)

    # Expiry categories (same as expiry_alert_list)
    expired_products = Product.objects.filter(expiry_date__lt=today)
    today_expiring = Product.objects.filter(expiry_date=today)
    soon_expiring = Product.objects.filter(expiry_date__range=[tomorrow, three_days])
    upcoming_expiry = Product.objects.filter(expiry_date__range=[three_days + timedelta(days=1), week_later])
    thirty_days_expiring = Product.objects.filter(expiry_date__range=[week_later + timedelta(days=1), thirty_days_later])

    # Calculate counts
    expired_count = expired_products.count()
    near_expiry_count = today_expiring.count() + soon_expiring.count()

    # Update session counts
    request.session['expired_count'] = expired_count
    request.session['near_expiry_count'] = near_expiry_count
    request.session.modified = True  # Ensure session is updated
    
    # Orders Status Distribution
    order_status_count = {
        "Pending": orders.filter(status="Pending").count(),
        "OrderConfirmed": orders.filter(status="Order Confirmed").count(),
        "OutforDelivery": orders.filter(status="Out for Delivery").count(),
        "Delivered": orders.filter(status="Delivered").count(),
    }

     # Product production data for the chart
    product_productions = ProductProduction.objects.all()
    production_data = defaultdict(list)

    for production in product_productions:
        production_data[production.production_date].append({
            'product_name': production.product_name.capitalize(),  # Convert product name to uppercase
            'quantity_produced': production.quantity_produced,
        })

    # Prepare data for the chart, sorting by production_date in ascending order
    production_labels = []
    production_quantities = []
    production_dates = []

    sorted_production_dates = sorted(production_data.keys())

    for production_date in sorted_production_dates:
        for entry in production_data[production_date]:
            production_labels.append(f"{entry['product_name']} ({production_date.strftime('%m-%d')})")
            production_quantities.append(entry['quantity_produced'])
            production_dates.append(production_date)

    # Sales Data - Total Sales (for total sales analysis)
    total_sales = orders.aggregate(total_sales=Sum(F('product__price') * F('quantity')))['total_sales'] or 0

    # Highest & Lowest Sales Orders
    sales_orders = orders.annotate(order_sales=F('product__price') * F('quantity'))
    
    highest_sales_order = sales_orders.order_by('-order_sales').first()
    lowest_sales_order = sales_orders.order_by('order_sales').first()

    highest_sales = highest_sales_order.order_sales if highest_sales_order else 0
    highest_sales_product = highest_sales_order.product.name if highest_sales_order else 'N/A'
    highest_sales_quantity = highest_sales_order.quantity if highest_sales_order else 0
    highest_sales_unit = highest_sales_order.product.unit if highest_sales_order else 'N/A'

    lowest_sales = lowest_sales_order.order_sales if lowest_sales_order else 0
    lowest_sales_product = lowest_sales_order.product.name if lowest_sales_order else 'N/A'
    lowest_sales_quantity = lowest_sales_order.quantity if lowest_sales_order else 0
    lowest_sales_unit = lowest_sales_order.product.unit if lowest_sales_order else 'N/A'

    # Total Orders (Count of all orders)
    total_orders = orders.count()

    # Context for rendering the dashboard
    context = {
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
        "today_expiring": today_expiring,
        "soon_expiring": soon_expiring,
        "upcoming_expiry": upcoming_expiry,
        "thirty_days_expiring": thirty_days_expiring,
        'expired_count': expired_count,
        'near_expiry_count': near_expiry_count,
        'today': today,
        "order_status_count": order_status_count,
        "production_labels": production_labels,
        "production_quantities": production_quantities,
        "production_dates": production_dates,
    }

    return render(request, "ecom/admin_dashboard.html", context)

# Add new product production record view
def add_product_production_view(request):
    if request.method == 'POST':
        # Handle form submission and create a new production record
        product_name = request.POST.get('product_name').strip().lower()  # Ensure product name is in lowercase
        product_unit = request.POST.get('product_unit').strip().lower()  # Ensure unit is in lowercase
        quantity_produced = request.POST.get('quantity_produced')
        production_date = request.POST.get('production_date')

        # Create and save a new ProductProduction instance
        new_production = ProductProduction(
            product_name=product_name,
            product_unit=product_unit,
            quantity_produced=quantity_produced,
            production_date=production_date
        )
        new_production.save()

        # Redirect to the product production list page after saving
        return redirect('product-production-list')

    # Pass today's date to the template for max date validation
    context = {'today': now().date()}
    return render(request, 'ecom/add_product_production.html', context)

# Edit existing product production record view
def edit_product_production_view(request, production_id):
    # Get the production record
    production = get_object_or_404(ProductProduction, id=production_id)

    if request.method == 'POST':
        # Get form data and update the production record
        product_name = request.POST.get('product_name').strip().lower()  # Standardize product name to lowercase
        quantity_produced = request.POST.get('quantity_produced')
        production_date = request.POST.get('production_date')

        # Update production record with the new data
        production.product_name = product_name
        production.quantity_produced = quantity_produced
        production.production_date = production_date
        production.save()

        return redirect('product-production-list')

    # Pass production to the template
    context = {
        'production': production,
    }
    return render(request, 'ecom/edit_product_production.html', context)
# Delete product production record view
def delete_product_production_view(request, production_id):
    # Get the production record and handle deletion
    production = get_object_or_404(ProductProduction, id=production_id)
    if request.method == 'POST':
        # Delete the production record
        production.delete()
        return redirect('product-production-list')  # Redirect to refresh the list

    # If not a POST request, redirect to the list page directly
    return redirect('product-production-list')

# Product production list view: Displays all product production records and totals
from datetime import date

def product_production_list_view(request):
    # Get all product production records
    product_productions = ProductProduction.objects.all()

    # Calculate total quantity produced for each product by date
    product_totals = {}
    for production in product_productions:
        product_name = production.product_name.upper()
        product_unit = production.product_unit
        production_date = production.production_date
        quantity_produced = production.quantity_produced

        # Initialize total quantity if not already present for the product
        if product_name not in product_totals:
            product_totals[product_name] = {
                'total_quantity': 0,
                'product_unit': product_unit,  # Store the unit for consistency
                'dates': {}
            }

        # Add quantity to the total for that product
        product_totals[product_name]['total_quantity'] += quantity_produced

        # Track the quantity produced for each specific date
        if production_date not in product_totals[product_name]['dates']:
            product_totals[product_name]['dates'][production_date] = 0
        product_totals[product_name]['dates'][production_date] += quantity_produced

    # Pass product production details to the template
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
    # Get all products ordered by production date (newest first)
    products = models.Product.objects.all().order_by('-date_added')
    
    # Format the production date for each product
    for product in products:
        product.formatted_date_added = product.date_added.strftime("%Y-%m-%d") if product.date_added else None


    
    context = {
        "products": products,
        "total_products": len(products),
    }
    
    return render(request, "ecom/admin_products.html", context)

@login_required(login_url="adminlogin")
def admin_add_product_view(request):
    productForm = forms.ProductForm()
    
    if request.method == "POST":
        productForm = forms.ProductForm(request.POST, request.FILES)
        if productForm.is_valid():
            # Get the cleaned data from the form
            product = productForm.save(commit=False)
            
            # Strip spaces and convert product name to lowercase
            product.product_name = product.name.strip().lower()
            
            # Save the new product
            product.save()
            
            # Update notification counts
            today = now().date()
            three_days = today + timedelta(days=3)
            
            # Calculate new counts
            expired_count = models.Product.objects.filter(expiry_date__lt=today).count()
            today_expiring = models.Product.objects.filter(expiry_date=today).count()
            soon_expiring = models.Product.objects.filter(
                expiry_date__range=[today + timedelta(days=1), three_days]
            ).count()
            
            # Update session
            request.session['expired_count'] = expired_count
            request.session['near_expiry_count'] = today_expiring + soon_expiring
            request.session.modified = True
            
            return HttpResponseRedirect(reverse("admin-products"))
    
    return render(request, "ecom/admin_add_products.html", {"productForm": productForm})


# delete product
@login_required(login_url="adminlogin")
def delete_product_view(request, pk):
    models.Product.objects.get(id=pk).delete()

    # Update session expiry counts
    today = now().date()
    request.session['expired_count'] = models.Product.objects.filter(expiry_date__lt=today).count()
    request.session['near_expiry_count'] = models.Product.objects.filter(
        expiry_date__range=[today, today + timedelta(days=3)]
    ).count()
    request.session.modified = True  # Ensure session updates

    return redirect("admin-products")


@login_required(login_url="adminlogin")
def update_product_view(request, pk):
    product = models.Product.objects.get(id=pk)
    productForm = forms.ProductForm(instance=product)

    if request.method == "POST":
        productForm = forms.ProductForm(request.POST, request.FILES, instance=product)
        if productForm.is_valid():
            # Get the cleaned data from the form before saving
            product = productForm.save(commit=False)
            
            # Strip spaces and convert product name to lowercase
            product.product_name = product.name.strip().lower()
            
            # Save the updated product
            product.save()
            
            # Update notification counts
            today = now().date()
            three_days = today + timedelta(days=3)
            
            # Calculate new counts
            expired_count = models.Product.objects.filter(expiry_date__lt=today).count()
            today_expiring = models.Product.objects.filter(expiry_date=today).count()
            soon_expiring = models.Product.objects.filter(
                expiry_date__range=[today + timedelta(days=1), three_days]
            ).count()
            
            # Update session
            request.session['expired_count'] = expired_count
            request.session['near_expiry_count'] = today_expiring + soon_expiring
            request.session.modified = True
            
            return redirect("admin-products")

    return render(request, "ecom/admin_update_product.html", {"productForm": productForm})
# views.py

@login_required(login_url="adminlogin")
def expiry_alert_list(request): 
    today = now().date()
    tomorrow = today + timedelta(days=1)
    three_days = today + timedelta(days=3)
    week_later = today + timedelta(days=7)
    thirty_days = today + timedelta(days=30)

    # Get products in different expiry categories
    expired_products = models.Product.objects.filter(expiry_date__lt=today).order_by('expiry_date')
    today_expiring = models.Product.objects.filter(expiry_date=today).order_by('expiry_date')
    soon_expiring = models.Product.objects.filter(expiry_date__range=[tomorrow, three_days]).order_by('expiry_date')
    upcoming_expiry = models.Product.objects.filter(expiry_date__range=[three_days + timedelta(days=1), week_later]).order_by('expiry_date')
    thirty_days_expiry = models.Product.objects.filter(expiry_date__range=[week_later + timedelta(days=1), thirty_days]).order_by('expiry_date')

    # Calculate counts
    expired_count = expired_products.count()
    near_expiry_count = today_expiring.count() + soon_expiring.count()

    # Update session only if counts have changed
    if request.session.get('expired_count') != expired_count or request.session.get('near_expiry_count') != near_expiry_count:
        request.session['expired_count'] = expired_count
        request.session['near_expiry_count'] = near_expiry_count
        request.session.modified = True  # Ensures session updates

    context = { 
        'expired_products': expired_products, 
        'today_expiring': today_expiring, 
        'soon_expiring': soon_expiring, 
        'upcoming_expiry': upcoming_expiry, 
        'thirty_days_expiry': thirty_days_expiry, 
        'critical_count': expired_count + near_expiry_count,  # Total count
        'today': today, 
    } 

    return render(request, "ecom/expiry_alerts.html", context)




@login_required(login_url="adminlogin")
def admin_view_booking_view(request):
    # Fetch orders and associated products/customers
    orders = models.Orders.objects.all().order_by('-order_date')
    ordered_products = []
    ordered_bys = []
    for order in orders:
        ordered_product = models.Product.objects.all().filter(id=order.product.id)
        ordered_by = models.Customer.objects.all().filter(id=order.customer.id)
        ordered_products.append(ordered_product)
        ordered_bys.append(ordered_by)

    # Render booking page
    return render(request, "ecom/admin_view_booking.html", {"data": zip(ordered_products, ordered_bys, orders)})

@login_required(login_url="adminlogin")
def delete_order_view(request, pk):
    # Delete order
    order = models.Orders.objects.get(id=pk)
    order.delete()
    return redirect("admin-view-booking")


@login_required(login_url="adminlogin")
def update_order_view(request, pk):
    # Get order and initialize form
    order = models.Orders.objects.get(id=pk)
    orderForm = forms.OrderForm(instance=order)

    if request.method == "POST":
        # Handle form submission and update order status
        orderForm = forms.OrderForm(request.POST, instance=order)
        if orderForm.is_valid():
            orderForm.save()
            return redirect("admin-view-booking")

    # Render form
    return render(request, "ecom/update_order.html", {"orderForm": orderForm})



# ---------------------------------------------------------------------------------
# ------------------------ PUBLIC CUSTOMER RELATED VIEWS START ---------------------
# ---------------------------------------------------------------------------------from django.shortcuts import redirect, get_object_or_404, render


def add_to_cart(request, product_id):
    # Ensure user is authenticated
    if not request.user.is_authenticated:
        return redirect("customerlogin")

    # Get the product and customer from the database
    product = get_object_or_404(Product, id=product_id)
    customer = get_object_or_404(Customer, user=request.user)

    # Check if the product is already in the cart
    existing_cart_item = Cart.objects.filter(product=product).first()

    if existing_cart_item:
        return redirect("cart")
    
    Cart.objects.create(customer=customer, product=product, quantity=1)

    return redirect("cart")



# cart view with stock validation
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

    # Recalculate total after any adjustments
    total = sum(item.product.price * item.quantity for item in cart_items)
    product_count_in_cart = cart_items.count()

    return render(request, "ecom/cart.html", {
        "cart_items": cart_items,
        "total": total,
        "product_count_in_cart": product_count_in_cart,
    })


def remove_from_cart_view(request, pk):
    # Remove item from the cart for authenticated user
    if not request.user.is_authenticated:
        return redirect("customerlogin")

    # Get the cart item to be removed
    cart_item = get_object_or_404(Cart, id=pk)

    # Ensure that the cart item belongs to the logged-in user
    if cart_item.customer.user != request.user:
        return redirect("cart")  # Prevent unauthorized removal

 
    cart_item.delete()

    return redirect("cart")

@login_required(login_url="customerlogin")
@user_passes_test(is_customer)
def customer_home_view(request):
    # Get all products
    products = Product.objects.all()

    # Get current date to compare expiry date
    today = timezone.now().date()
    three_days_later = today + timedelta(days=3)

    # Identify out-of-stock products based on order statuses
    out_of_stock_products = products.filter(
        orders__status__in=["Pending", "Order Confirmed", "Out for Delivery", "Delivered"]
    ).distinct()

    # Filter expired products or products expiring within the next 3 days
    expired_or_near_expiry_products = products.filter(expiry_date__lte=three_days_later)

    # Products that are still in stock and not expired or near expiry
    in_stock_products = products.exclude(id__in=out_of_stock_products).exclude(id__in=expired_or_near_expiry_products)

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



#  payment success view 
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
    # View to display the orders of the logged-in customer
    customer = models.Customer.objects.get(user_id=request.user.id)
    orders = models.Orders.objects.filter(customer=customer).select_related('product')  # Optimized query
    
    return render(
        request,
        "ecom/my_order.html",
        {"orders": orders}  
    )

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
            return redirect(next_url)  # Redirect to 'next' or fallback

    else:
        # Prefill the forms with the current user and customer data
        userForm = forms.EditProfileForm(instance=user)  # Without password field
        customerForm = forms.EditCustomerForm(instance=customer)

    return render(request, "ecom/edit_profile.html", {"userForm": userForm, "customerForm": customerForm})

# --------------for discharge customer bill (pdf) download and printing----------------
def render_to_pdf(template_src, context_dict):
    try:
        template = get_template(template_src)
        html = template.render(context_dict)
        result = io.BytesIO()
        pdf = pisa.pisaDocument(io.BytesIO(html.encode("utf-8")), result)  # Consider utf-8 for broader character support

        if not pdf.err:
            return HttpResponse(result.getvalue(), content_type="application/pdf")
        else:
            # Optionally handle the error by logging or returning an appropriate message
            return HttpResponse("Error generating PDF", status=400)

    except Exception as e:
        # Handle unexpected errors
        return HttpResponse(f"An error occurred: {str(e)}", status=500)



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


#Contactus & About us
def contactus_view(request):
    return render(request, "ecom/contactus.html")

