from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------

class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    order = models.PositiveSmallIntegerField(default=0, help_text="Display order on the menu page")

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class DietaryTag(models.TextChoices):
    VEGETARIAN  = 'vegetarian',  'Vegetarian'
    VEGAN       = 'vegan',       'Vegan'
    GLUTEN_FREE = 'gluten_free', 'Gluten-Free'
    SPICY       = 'spicy',       'Spicy'
    DAIRY_FREE  = 'dairy_free',  'Dairy-Free'


class MenuItem(models.Model):
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    name        = models.CharField(max_length=100)
    description = models.TextField()
    price       = models.DecimalField(max_digits=6, decimal_places=2)
    image       = models.ImageField(upload_to='menu_images/', blank=True)
    is_featured = models.BooleanField(default=False, help_text="Show on the home page as a featured dish")
    dietary_tags = models.CharField(
        max_length=200, blank=True,
        help_text="Comma-separated list of tags, e.g. vegetarian,vegan"
    )
    prep_time_minutes = models.PositiveSmallIntegerField(
        default=20,
        help_text="Estimated preparation time in minutes shown to the customer"
    )

    class Meta:
        ordering = ['category__order', 'name']

    def __str__(self):
        return self.name

    def get_dietary_tags_list(self):
        """Return dietary tags as a cleaned list of strings."""
        if not self.dietary_tags:
            return []
        return [t.strip() for t in self.dietary_tags.split(',') if t.strip()]

    def get_dietary_tag_labels(self):
        """Return human-readable labels for dietary tags."""
        mapping = dict(DietaryTag.choices)
        return [mapping.get(t, t.title()) for t in self.get_dietary_tags_list()]


# ---------------------------------------------------------------------------
# Reservation
# ---------------------------------------------------------------------------

class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'

    name       = models.CharField(max_length=100)
    email      = models.EmailField(blank=True)
    contact    = models.CharField(max_length=20)
    time       = models.DateTimeField()
    count      = models.IntegerField(verbose_name="Party size")
    notes      = models.TextField(blank=True)
    status     = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    # Optional link to a menu item (e.g. pre-ordering) — nullable FK replaces the old CharField
    item       = models.ForeignKey(
        MenuItem, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='reservations',
        help_text="Optional menu item associated with this reservation"
    )

    class Meta:
        ordering = ['-time']

    def __str__(self):
        return f"{self.name} — {self.time:%Y-%m-%d %H:%M} ({self.count} guests)"


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

class Order(models.Model):
    class OrderType(models.TextChoices):
        DINE_IN  = 'dine_in',  'Dine-in'
        TAKEAWAY = 'takeaway', 'Takeaway'

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        PREPARING = 'preparing', 'Preparing'
        READY     = 'ready',     'Ready'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    customer_name    = models.CharField(max_length=100)
    email            = models.EmailField()
    phone            = models.CharField(max_length=20, blank=True)
    order_type       = models.CharField(max_length=20, choices=OrderType.choices, default=OrderType.DINE_IN)
    # Takeaway: delivery address; Dine-in: not required
    delivery_address = models.TextField(blank=True)
    # Dine-in: party size; Takeaway: not required
    party_size       = models.PositiveSmallIntegerField(null=True, blank=True)
    status           = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_price      = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    created_at       = models.DateTimeField(auto_now_add=True)
    notes            = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.pk} — {self.customer_name} ({self.order_type})"

    def recalculate_total(self):
        """Recompute total from actual item prices — call before save."""
        self.total_price = sum(
            item.unit_price * item.quantity for item in self.order_items.all()
        )

    @property
    def estimated_prep_minutes(self):
        """Max prep time across all items (they cook in parallel, not sequence)."""
        times = [oi.menu_item.prep_time_minutes for oi in self.order_items.select_related('menu_item').all()]
        return max(times) if times else 20

    @property
    def eta(self):
        """Datetime when order should be ready."""
        return self.created_at + __import__('datetime').timedelta(minutes=self.estimated_prep_minutes)

    @property
    def minutes_remaining(self):
        """Minutes left until ETA. Negative means overdue."""
        from django.utils import timezone as tz
        import datetime
        delta = self.eta - tz.now()
        return max(0, int(delta.total_seconds() // 60))


class OrderItem(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    menu_item  = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='order_items')
    quantity   = models.PositiveSmallIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)  # snapshot at order time

    def __str__(self):
        return f"{self.quantity}× {self.menu_item.name}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


# ---------------------------------------------------------------------------
# Business hours (simple model-based approach)
# ---------------------------------------------------------------------------

class BusinessHours(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    day_of_week  = models.PositiveSmallIntegerField(choices=DAY_CHOICES, unique=True)
    open_time    = models.TimeField(null=True, blank=True, help_text="Leave blank for closed day")
    close_time   = models.TimeField(null=True, blank=True)
    is_closed    = models.BooleanField(default=False)

    class Meta:
        ordering = ['day_of_week']
        verbose_name_plural = "Business hours"

    def __str__(self):
        day_name = dict(self.DAY_CHOICES).get(self.day_of_week, str(self.day_of_week))
        if self.is_closed:
            return f"{day_name}: Closed"
        return f"{day_name}: {self.open_time} – {self.close_time}"
