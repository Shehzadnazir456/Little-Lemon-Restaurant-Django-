"""
Clean initial migration for the full Little Lemon schema.
Generated manually to replace the original SQLite-era migrations.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        # ------------------------------------------------------------------
        # Category
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id',    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name',  models.CharField(max_length=60, unique=True)),
                ('slug',  models.SlugField(max_length=60, unique=True)),
                ('order', models.PositiveSmallIntegerField(default=0, help_text='Display order on the menu page')),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['order', 'name'],
            },
        ),
        # ------------------------------------------------------------------
        # MenuItem
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('id',           models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name',         models.CharField(max_length=100)),
                ('description',  models.TextField()),
                ('price',        models.DecimalField(decimal_places=2, max_digits=6)),
                ('image',        models.ImageField(blank=True, upload_to='menu_images/')),
                ('is_featured',  models.BooleanField(default=False, help_text='Show on the home page as a featured dish')),
                ('dietary_tags', models.CharField(blank=True, max_length=200, help_text='Comma-separated list of tags')),
                ('category',     models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='items', to='restaurant.category')),
            ],
            options={
                'ordering': ['category__order', 'name'],
            },
        ),
        # ------------------------------------------------------------------
        # BusinessHours
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='BusinessHours',
            fields=[
                ('id',          models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_week', models.PositiveSmallIntegerField(choices=[(0,'Monday'),(1,'Tuesday'),(2,'Wednesday'),(3,'Thursday'),(4,'Friday'),(5,'Saturday'),(6,'Sunday')], unique=True)),
                ('open_time',   models.TimeField(blank=True, null=True, help_text='Leave blank for closed day')),
                ('close_time',  models.TimeField(blank=True, null=True)),
                ('is_closed',   models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'Business hours',
                'ordering': ['day_of_week'],
            },
        ),
        # ------------------------------------------------------------------
        # Reservation
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name',       models.CharField(max_length=100)),
                ('email',      models.EmailField(blank=True)),
                ('contact',    models.CharField(max_length=20)),
                ('time',       models.DateTimeField()),
                ('count',      models.IntegerField(verbose_name='Party size')),
                ('notes',      models.TextField(blank=True)),
                ('status',     models.CharField(choices=[('pending','Pending'),('confirmed','Confirmed'),('cancelled','Cancelled')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('item',       models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reservations', to='restaurant.menuitem', help_text='Optional menu item associated with this reservation')),
            ],
            options={
                'ordering': ['-time'],
            },
        ),
        # ------------------------------------------------------------------
        # Order
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id',               models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name',    models.CharField(max_length=100)),
                ('email',            models.EmailField()),
                ('phone',            models.CharField(blank=True, max_length=20)),
                ('order_type',       models.CharField(choices=[('dine_in','Dine-in'),('takeaway','Takeaway')], default='dine_in', max_length=20)),
                ('delivery_address', models.TextField(blank=True)),
                ('party_size',       models.PositiveSmallIntegerField(blank=True, null=True)),
                ('status',           models.CharField(choices=[('pending','Pending'),('preparing','Preparing'),('ready','Ready'),('completed','Completed'),('cancelled','Cancelled')], default='pending', max_length=20)),
                ('total_price',      models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('created_at',       models.DateTimeField(auto_now_add=True)),
                ('notes',            models.TextField(blank=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        # ------------------------------------------------------------------
        # OrderItem
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity',   models.PositiveSmallIntegerField(default=1)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=6)),
                ('menu_item',  models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='restaurant.menuitem')),
                ('order',      models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='restaurant.order')),
            ],
        ),
    ]
