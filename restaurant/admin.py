from django.contrib import admin
from .models import Category, MenuItem, Reservation, Order, OrderItem, BusinessHours


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['unit_price']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display   = ['name', 'category', 'price', 'is_featured', 'dietary_tags']
    list_filter    = ['category', 'is_featured']
    search_fields  = ['name', 'description']
    list_editable  = ['is_featured', 'price']


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display  = ['name', 'time', 'count', 'status', 'contact']
    list_filter   = ['status']
    search_fields = ['name', 'contact', 'email']
    list_editable = ['status']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display   = ['id', 'customer_name', 'email', 'order_type', 'status', 'total_price', 'created_at']
    list_filter    = ['status', 'order_type']
    search_fields  = ['customer_name', 'email']
    list_editable  = ['status']
    inlines        = [OrderItemInline]


@admin.register(BusinessHours)
class BusinessHoursAdmin(admin.ModelAdmin):
    list_display = ['day_of_week', 'open_time', 'close_time', 'is_closed']
    list_editable = ['open_time', 'close_time', 'is_closed']
