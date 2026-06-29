from django.urls import path
from . import views

urlpatterns = [
    # ── Public pages (existing names preserved) ────────────────────────────
    path('',            views.home_view,        name='home'),
    path('menu/',       views.menu_view,         name='menu'),
    path('about/',      views.about_view,        name='about'),
    path('contact/',    views.contact_view,      name='contact'),
    path('reservation/', views.reservation_view, name='reservation'),

    # ── Cart ───────────────────────────────────────────────────────────────
    path('cart/',                          views.cart_view,   name='cart_view'),
    path('cart/add/<int:item_id>/',        views.cart_add,    name='cart_add'),
    path('cart/remove/<int:item_id>/',     views.cart_remove, name='cart_remove'),
    path('cart/update/<int:item_id>/',     views.cart_update, name='cart_update'),

    # ── Orders ─────────────────────────────────────────────────────────────
    path('checkout/',                             views.checkout_view,          name='checkout'),
    path('order-confirmation/<int:order_id>/',    views.order_confirmation_view, name='order_confirmation'),
    path('order-status/',                         views.order_status_view,      name='order_status'),
    path('order-status/<int:order_id>/api/',      views.order_status_api,       name='order_status_api'),

    # ── Admin / dashboard ──────────────────────────────────────────────────
    path('admin-login/',   views.admin_login_view,      name='admin_login'),
    path('dashboard/',     views.dashboard_view,         name='dashboard'),
    path('dashboard/orders/',        views.dashboard_orders_view,       name='dashboard_orders'),
    path('dashboard/reservations/',  views.dashboard_reservations_view, name='dashboard_reservations'),
    path('dashboard/orders/<int:order_id>/status/',           views.update_order_status_view,      name='update_order_status'),
    path('dashboard/reservations/<int:reservation_id>/status/', views.update_reservation_status_view, name='update_reservation_status'),
    path('dashboard/logout/', views.dashboard_logout_view, name='dashboard_logout'),
]
