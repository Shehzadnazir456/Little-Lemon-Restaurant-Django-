"""
Views for the Little Lemon restaurant site.

Public routes  : home, about, contact, menu, reservation, cart, checkout,
                 order_confirmation, order_status
Auth/dashboard : admin_login_view, dashboard_view, dashboard_orders,
                 dashboard_reservations, update_order_status,
                 update_reservation_status, dashboard_logout
"""

import datetime
import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    OrderForm,
    OrderLookupForm,
    OrderStatusForm,
    ReservationForm,
    ReservationStatusForm,
)
from .models import (
    BusinessHours,
    Category,
    MenuItem,
    Order,
    OrderItem,
    Reservation,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def staff_required(view_func):
    """Decorator: user must be authenticated AND is_staff."""
    decorated = login_required(
        user_passes_test(lambda u: u.is_staff, login_url='/admin-login/')(view_func),
        login_url='/admin-login/',
    )
    return decorated


def _get_cart(request):
    """Return the session cart dict {str(menu_item_id): quantity}."""
    return request.session.get('cart', {})


def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def _get_is_open(business_hours_qs):
    """Return True if the restaurant is currently open."""
    now_local = timezone.localtime(timezone.now())
    today = now_local.weekday()        # 0 = Monday
    current_time = now_local.time()
    try:
        bh = business_hours_qs.get(day_of_week=today)
        if bh.is_closed or bh.open_time is None:
            return False
        return bh.open_time <= current_time <= bh.close_time
    except BusinessHours.DoesNotExist:
        return False


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

def home_view(request):
    featured = MenuItem.objects.filter(is_featured=True).select_related('category')[:4]
    business_hours = BusinessHours.objects.all()
    is_open = _get_is_open(business_hours)
    return render(request, 'restaurant/home.html', {
        'featured_items': featured,
        'business_hours': business_hours,
        'is_open': is_open,
    })


def about_view(request):
    return render(request, 'restaurant/about.html')


def contact_view(request):
    business_hours = BusinessHours.objects.all()
    is_open = _get_is_open(business_hours)
    return render(request, 'restaurant/contact.html', {
        'business_hours': business_hours,
        'is_open': is_open,
    })


def menu_view(request):
    categories = Category.objects.prefetch_related('items').all()
    active_category = request.GET.get('category', '')
    all_items = MenuItem.objects.select_related('category').all()
    if active_category:
        all_items = all_items.filter(category__slug=active_category)
    cart = _get_cart(request)
    return render(request, 'restaurant/menu.html', {
        'categories': categories,
        'menu_items': all_items,
        'active_category': active_category,
        'cart': cart,
        'cart_count': sum(cart.values()),
    })


def reservation_view(request):
    item_id = request.GET.get('item', '')
    initial = {}
    if item_id:
        try:
            initial['item'] = MenuItem.objects.get(pk=int(item_id))
        except (MenuItem.DoesNotExist, ValueError):
            pass

    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your reservation has been submitted successfully!")
            return redirect('reservation')
    else:
        form = ReservationForm(initial=initial)

    return render(request, 'restaurant/reservation.html', {'form': form})


# ---------------------------------------------------------------------------
# Cart (session-based, no login required)
# ---------------------------------------------------------------------------

@require_POST
def cart_add(request, item_id):
    item = get_object_or_404(MenuItem, pk=item_id)
    cart = _get_cart(request)
    key = str(item_id)
    cart[key] = cart.get(key, 0) + 1
    _save_cart(request, cart)
    messages.success(request, f'"{item.name}" added to your cart.')
    return redirect(request.META.get('HTTP_REFERER', 'menu'))


@require_POST
def cart_remove(request, item_id):
    cart = _get_cart(request)
    key = str(item_id)
    if key in cart:
        del cart[key]
        _save_cart(request, cart)
    return redirect('cart_view')


@require_POST
def cart_update(request, item_id):
    cart = _get_cart(request)
    key = str(item_id)
    qty = int(request.POST.get('quantity', 1))
    if qty > 0:
        cart[key] = qty
    else:
        cart.pop(key, None)
    _save_cart(request, cart)
    return redirect('cart_view')


def cart_view(request):
    cart = _get_cart(request)
    items = []
    subtotal = Decimal('0.00')
    for item_id_str, qty in cart.items():
        try:
            menu_item = MenuItem.objects.get(pk=int(item_id_str))
            line_total = menu_item.price * qty
            subtotal += line_total
            items.append({'menu_item': menu_item, 'quantity': qty, 'line_total': line_total})
        except MenuItem.DoesNotExist:
            pass
    return render(request, 'restaurant/cart.html', {
        'cart_items': items,
        'subtotal': subtotal,
        'cart_count': sum(cart.values()),
    })


# ---------------------------------------------------------------------------
# Checkout / Order
# ---------------------------------------------------------------------------

def checkout_view(request):
    cart = _get_cart(request)
    if not cart:
        messages.warning(request, 'Your cart is empty. Add some items first!')
        return redirect('menu')

    # Build preview items (server-side prices)
    items = []
    subtotal = Decimal('0.00')
    for item_id_str, qty in cart.items():
        try:
            menu_item = MenuItem.objects.get(pk=int(item_id_str))
            line_total = menu_item.price * qty
            subtotal += line_total
            items.append({'menu_item': menu_item, 'quantity': qty, 'line_total': line_total})
        except MenuItem.DoesNotExist:
            pass

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            # Server-side total — never trust the client
            order.total_price = subtotal
            order.save()

            # Create OrderItems
            for entry in items:
                OrderItem.objects.create(
                    order=order,
                    menu_item=entry['menu_item'],
                    quantity=entry['quantity'],
                    unit_price=entry['menu_item'].price,
                )

            # Clear cart
            request.session.pop('cart', None)
            request.session.modified = True

            # Confirmation email (falls back to console in dev)
            _send_order_confirmation(order, items)

            return redirect('order_confirmation', order_id=order.pk)
    else:
        form = OrderForm()

    return render(request, 'restaurant/checkout.html', {
        'form': form,
        'cart_items': items,
        'subtotal': subtotal,
        'cart_count': sum(cart.values()),
    })


def order_confirmation_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    order_items = order.order_items.select_related('menu_item').all()
    return render(request, 'restaurant/order_confirmation.html', {
        'order': order,
        'order_items': order_items,
    })


def order_status_view(request):
    order = None
    form = OrderLookupForm(request.GET or None)
    if form.is_valid():
        try:
            order = Order.objects.prefetch_related('order_items__menu_item').get(
                pk=form.cleaned_data['order_id'],
                email__iexact=form.cleaned_data['email'],
            )
        except Order.DoesNotExist:
            messages.error(request, 'No order found with that order number and email address.')

    # Steps shown in the tracker UI (cancelled is handled separately)
    order_steps = [
        ('pending',   'Received'),
        ('preparing', 'Preparing'),
        ('ready',     'Ready'),
        ('completed', 'Delivered'),
    ]
    step_keys = [s[0] for s in order_steps]
    order_step_index = step_keys.index(order.status) if order and order.status in step_keys else 0

    return render(request, 'restaurant/order_status.html', {
        'form':             form,
        'order':            order,
        'order_items':      order.order_items.select_related('menu_item').all() if order else [],
        'order_steps':      order_steps,
        'order_step_index': order_step_index,
    })

    return render(request, 'restaurant/order_status.html', {
        'form': form,
        'order': order,
        'order_items': order.order_items.select_related('menu_item').all() if order else [],
    })


def order_status_api(request, order_id):
    """
    JSON endpoint polled by the live tracker every 15 s.
    Returns status, ETA info, and item prep times.
    No authentication — customers use order_id + email as a shared secret.
    """
    email = request.GET.get('email', '').strip()
    if not email:
        return JsonResponse({'error': 'email required'}, status=400)

    try:
        order = Order.objects.prefetch_related('order_items__menu_item').get(
            pk=order_id,
            email__iexact=email,
        )
    except Order.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)

    now = timezone.now()
    eta_dt = order.eta
    seconds_remaining = max(0, int((eta_dt - now).total_seconds()))
    total_seconds = order.estimated_prep_minutes * 60
    elapsed_seconds = max(0, int((now - order.created_at).total_seconds()))
    progress_pct = min(100, int((elapsed_seconds / total_seconds) * 100)) if total_seconds else 100

    # For completed/cancelled, always 100% progress
    if order.status in (Order.Status.COMPLETED, Order.Status.CANCELLED, Order.Status.READY):
        progress_pct = 100
        seconds_remaining = 0

    items = [
        {
            'name': oi.menu_item.name,
            'quantity': oi.quantity,
            'prep_minutes': oi.menu_item.prep_time_minutes,
            'subtotal': str(oi.subtotal),
        }
        for oi in order.order_items.all()
    ]

    return JsonResponse({
        'order_id':          order.pk,
        'status':            order.status,
        'status_display':    order.get_status_display(),
        'order_type':        order.order_type,
        'order_type_display': order.get_order_type_display(),
        'eta_iso':           eta_dt.isoformat(),
        'seconds_remaining': seconds_remaining,
        'progress_pct':      progress_pct,
        'total_minutes':     order.estimated_prep_minutes,
        'items':             items,
        'total_price':       str(order.total_price),
        'created_at_iso':    order.created_at.isoformat(),
    })


def _send_order_confirmation(order, items):
    lines = [f"Hi {order.customer_name},\n",
             f"Thank you for your order! Here's your summary:\n",
             f"Order #{order.pk}\n"]
    for entry in items:
        lines.append(f"  {entry['quantity']}× {entry['menu_item'].name}  ${entry['line_total']:.2f}")
    lines.append(f"\nTotal: ${order.total_price:.2f}")
    lines.append(f"Order type: {order.get_order_type_display()}")
    lines.append(f"\nYou can check your order status at: {settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'our website'}/order-status/")
    lines.append("\nThank you for choosing Little Lemon!")
    body = '\n'.join(lines)
    try:
        send_mail(
            subject=f'Little Lemon — Order #{order.pk} confirmed',
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            fail_silently=True,
        )
    except Exception:
        pass  # Never crash on email failure


# ---------------------------------------------------------------------------
# Admin login / logout (custom page, uses Django auth underneath)
# ---------------------------------------------------------------------------

def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            error = 'Invalid credentials or insufficient permissions.'

    return render(request, 'restaurant/admin_login.html', {'error': error})


def dashboard_logout_view(request):
    logout(request)
    return redirect('admin_login')


# ---------------------------------------------------------------------------
# Custom dashboard — staff only
# ---------------------------------------------------------------------------

@staff_required
def dashboard_view(request):
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.datetime.combine(today, datetime.time.min))
    today_end   = timezone.make_aware(datetime.datetime.combine(today, datetime.time.max))

    orders_today       = Order.objects.filter(created_at__range=(today_start, today_end))
    reservations_today = Reservation.objects.filter(time__range=(today_start, today_end))
    revenue_today      = sum(
        o.total_price for o in orders_today.filter(status=Order.Status.COMPLETED)
    )

    return render(request, 'restaurant/dashboard.html', {
        'total_orders_today':       orders_today.count(),
        'total_reservations_today': reservations_today.count(),
        'revenue_today':            revenue_today,
        'recent_orders':            Order.objects.select_related().all()[:10],
        'recent_reservations':      Reservation.objects.select_related('item').all()[:10],
    })


@staff_required
def dashboard_orders_view(request):
    qs = Order.objects.all()
    status_filter = request.GET.get('status', '')
    type_filter   = request.GET.get('type', '')
    if status_filter:
        qs = qs.filter(status=status_filter)
    if type_filter:
        qs = qs.filter(order_type=type_filter)
    return render(request, 'restaurant/dashboard_orders.html', {
        'orders':         qs,
        'status_choices': Order.Status.choices,
        'type_choices':   Order.OrderType.choices,
        'status_filter':  status_filter,
        'type_filter':    type_filter,
        'status_forms':   {o.pk: OrderStatusForm(instance=o) for o in qs},
    })


@staff_required
def dashboard_reservations_view(request):
    qs = Reservation.objects.select_related('item').all()
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, 'restaurant/dashboard_reservations.html', {
        'reservations':   qs,
        'status_choices': Reservation.Status.choices,
        'status_filter':  status_filter,
        'status_forms':   {r.pk: ReservationStatusForm(instance=r) for r in qs},
    })


@staff_required
@require_POST
def update_order_status_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    form = OrderStatusForm(request.POST, instance=order)
    if form.is_valid():
        form.save()
        messages.success(request, f'Order #{order.pk} status updated to "{order.get_status_display()}".')
    return redirect('dashboard_orders')


@staff_required
@require_POST
def update_reservation_status_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id)
    form = ReservationStatusForm(request.POST, instance=reservation)
    if form.is_valid():
        form.save()
        messages.success(request, f'Reservation for "{reservation.name}" updated.')
    return redirect('dashboard_reservations')
