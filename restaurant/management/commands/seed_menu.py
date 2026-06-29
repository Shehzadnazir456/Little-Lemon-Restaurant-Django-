"""
Management command: python manage.py seed_menu

Seeds the database with categories, business hours, and 12 Mediterranean
menu items. Running it a second time is safe — it uses get_or_create so
existing records are not duplicated.
"""

from django.core.management.base import BaseCommand
from restaurant.models import Category, MenuItem, BusinessHours
import datetime


CATEGORIES = [
    {'name': 'Starters',  'slug': 'starters',  'order': 1},
    {'name': 'Mains',     'slug': 'mains',      'order': 2},
    {'name': 'Desserts',  'slug': 'desserts',   'order': 3},
    {'name': 'Drinks',    'slug': 'drinks',     'order': 4},
]

MENU_ITEMS = [
    # ── Starters ────────────────────────────────────────────────────────────
    {
        'category_slug': 'starters',
        'name': 'Greek Salad',
        'description': 'Crisp romaine, ripe tomatoes, Kalamata olives, cucumber, red onion, and generous crumbles of feta dressed in extra-virgin olive oil and dried oregano.',
        'price': '8.50',
        'is_featured': True,
        'dietary_tags': 'vegetarian,gluten_free',
        'image': 'menu_images/greek-salad.jpg',
        'prep_time_minutes': 8,
    },
    {
        'category_slug': 'starters',
        'name': 'Bruschetta',
        'description': 'Toasted sourdough rubbed with garlic, topped with slow-roasted cherry tomatoes, fresh basil, and a drizzle of aged balsamic glaze.',
        'price': '7.00',
        'is_featured': False,
        'dietary_tags': 'vegetarian',
        'image': 'menu_images/bruschetta.jpg',
        'prep_time_minutes': 10,
    },
    {
        'category_slug': 'starters',
        'name': 'Hummus Plate',
        'description': 'Silky homemade hummus swirled with tahini, topped with roasted chickpeas, smoked paprika, and a pool of olive oil. Served with warm pita bread.',
        'price': '7.50',
        'is_featured': False,
        'dietary_tags': 'vegan',
        'image': 'menu_images/hummus-plate.jpg',
        'prep_time_minutes': 5,
    },
    {
        'category_slug': 'starters',
        'name': 'Stuffed Vine Leaves',
        'description': 'Six hand-rolled vine leaves filled with herbed rice, toasted pine nuts, and currants, served with a cool tzatziki dipping sauce.',
        'price': '9.00',
        'is_featured': False,
        'dietary_tags': 'vegan',
        'image': 'menu_images/vine-leaves.jpg',
        'prep_time_minutes': 12,
    },
    # ── Mains ───────────────────────────────────────────────────────────────
    {
        'category_slug': 'mains',
        'name': 'Grilled Lamb Chops',
        'description': 'Two tender lamb chops marinated in rosemary, garlic, and lemon zest, grilled over charcoal. Served with roasted potatoes and a mint-yoghurt sauce.',
        'price': '24.00',
        'is_featured': True,
        'dietary_tags': 'gluten_free',
        'image': 'menu_images/lamb-chops.jpg',
        'prep_time_minutes': 35,
    },
    {
        'category_slug': 'mains',
        'name': 'Lemon Herb Chicken',
        'description': 'Free-range half chicken slow-roasted with preserved lemon, harissa, and a seven-herb chermoula. Served with saffron couscous and a side of fattoush.',
        'price': '18.50',
        'is_featured': True,
        'dietary_tags': 'gluten_free',
        'image': 'menu_images/lemon-chicken.jpg',
        'prep_time_minutes': 40,
    },
    {
        'category_slug': 'mains',
        'name': 'Falafel Wrap',
        'description': 'Crispy fried falafel, pickled red cabbage, cucumber, tomato, and a house tahini sauce wrapped in a warm whole-wheat flatbread.',
        'price': '12.00',
        'is_featured': False,
        'dietary_tags': 'vegan',
        'image': 'menu_images/falafel-wrap.jpg',
        'prep_time_minutes': 15,
    },
    {
        'category_slug': 'mains',
        'name': 'Seafood Pasta',
        'description': 'Al-dente linguine tossed with prawns, mussels, squid, cherry tomatoes, white wine, garlic, and a touch of chilli — finished with parsley and lemon.',
        'price': '21.00',
        'is_featured': False,
        'dietary_tags': 'dairy_free',
        'image': 'menu_images/seafood-pasta.jpg',
        'prep_time_minutes': 25,
    },
    # ── Desserts ─────────────────────────────────────────────────────────────
    {
        'category_slug': 'desserts',
        'name': 'Baklava',
        'description': 'Classic layered filo pastry packed with walnuts, pistachios, and cinnamon, soaked in orange-blossom honey syrup. Three pieces per serving.',
        'price': '7.00',
        'is_featured': False,
        'dietary_tags': 'vegetarian',
        'image': 'menu_images/baklava.jpg',
        'prep_time_minutes': 5,
    },
    {
        'category_slug': 'desserts',
        'name': 'Lemon Tart',
        'description': 'Buttery shortcrust shell filled with a sharp, velvety lemon curd and topped with torched Italian meringue and candied lemon zest.',
        'price': '8.00',
        'is_featured': True,
        'dietary_tags': 'vegetarian',
        'image': 'menu_images/lemon-tart.jpg',
        'prep_time_minutes': 8,
    },
    # ── Drinks ──────────────────────────────────────────────────────────────
    {
        'category_slug': 'drinks',
        'name': 'Mediterranean Lemonade',
        'description': 'Fresh-pressed lemons blended with rosewater, a hint of mint, and sparkling water. Lightly sweetened with raw cane sugar.',
        'price': '4.50',
        'is_featured': False,
        'dietary_tags': 'vegan,gluten_free',
        'image': 'menu_images/lemonade.jpg',
        'prep_time_minutes': 5,
    },
    {
        'category_slug': 'drinks',
        'name': 'Moroccan Mint Tea',
        'description': 'Traditional Maghrebi green tea brewed strong with generous bunches of fresh spearmint, poured tall for a beautiful froth. Naturally caffeine-light.',
        'price': '3.50',
        'is_featured': False,
        'dietary_tags': 'vegan,gluten_free',
        'image': 'menu_images/mint-tea.jpg',
        'prep_time_minutes': 5,
    },
]

BUSINESS_HOURS = [
    # (day_of_week, open_time, close_time, is_closed)
    (0, datetime.time(11, 0), datetime.time(22, 0), False),  # Monday
    (1, datetime.time(11, 0), datetime.time(22, 0), False),  # Tuesday
    (2, datetime.time(11, 0), datetime.time(22, 0), False),  # Wednesday
    (3, datetime.time(11, 0), datetime.time(22, 0), False),  # Thursday
    (4, datetime.time(11, 0), datetime.time(23, 0), False),  # Friday
    (5, datetime.time(9,  0), datetime.time(23, 0), False),  # Saturday
    (6, datetime.time(9,  0), datetime.time(22, 0), False),  # Sunday
]


class Command(BaseCommand):
    help = 'Seed the database with menu categories, items, and business hours.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding categories...')
        cat_map = {}
        for data in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                slug=data['slug'],
                defaults={'name': data['name'], 'order': data['order']},
            )
            cat_map[data['slug']] = cat
            status = 'created' if created else 'already exists'
            self.stdout.write(f'  Category "{cat.name}" — {status}')

        self.stdout.write('Seeding menu items...')
        for data in MENU_ITEMS:
            category = cat_map.get(data['category_slug'])
            item, created = MenuItem.objects.get_or_create(
                name=data['name'],
                defaults={
                    'category':          category,
                    'description':       data['description'],
                    'price':             data['price'],
                    'is_featured':       data['is_featured'],
                    'dietary_tags':      data['dietary_tags'],
                    'image':             data.get('image', ''),
                    'prep_time_minutes': data.get('prep_time_minutes', 20),
                },
            )
            status = 'created' if created else 'already exists'
            self.stdout.write(f'  MenuItem "{item.name}" — {status}')

        self.stdout.write('Seeding business hours...')
        for day, open_t, close_t, is_closed in BUSINESS_HOURS:
            bh, created = BusinessHours.objects.get_or_create(
                day_of_week=day,
                defaults={'open_time': open_t, 'close_time': close_t, 'is_closed': is_closed},
            )
            status = 'created' if created else 'already exists'
            self.stdout.write(f'  {bh} — {status}')

        self.stdout.write(self.style.SUCCESS('\nSeed complete!'))
