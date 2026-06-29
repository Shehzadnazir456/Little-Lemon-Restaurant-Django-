# 🍋 Little Lemon Restaurant

A full-featured, portfolio-ready Django restaurant website built from scratch — no CSS frameworks, no shortcuts. Every line of HTML, CSS, and Python is hand-written and intentional.

> **Tech stack:** Django 5 · PostgreSQL · python-decouple · Pillow · Vanilla JS · Custom CSS Grid/Flexbox

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Feature Deep-Dive](#feature-deep-dive)
3. [Data Models](#data-models)
4. [Requirements](#requirements)
5. [Setup & Installation](#setup--installation)
6. [Running Tests](#running-tests)
7. [Image Assets](#image-assets)
8. [URL Reference](#url-reference)
9. [Environment Variables](#environment-variables)
10. [Email Configuration](#email-configuration)

---

## Project Overview

Little Lemon is a Mediterranean restaurant site that covers every layer of a real production web app:

- A customer-facing website with browsable menu, session cart, and online ordering
- A live order tracker that polls the server every 15 seconds and counts down to the ETA
- A table reservation system with optional dish pre-ordering
- A custom staff dashboard for managing orders and reservations day-to-day
- Django Admin for menu and category management
- A complete custom CSS design system — colour palette, typography, spacing scale, responsive breakpoints — written by hand without Bootstrap or Tailwind

---

## Feature Deep-Dive

### Home Page

The home page is built as a proper restaurant landing page, not a placeholder.

- **Full-width hero section** with a background photograph, the restaurant name and tagline, an "Open Now / Currently Closed" status pill that reflects real business hours, and two call-to-action buttons (Book a Table, Explore Menu).
- **"Why Little Lemon" strip** — four feature cards (Fresh Every Day, Master Chefs, House-Made Everything, Family Atmosphere) built with CSS Grid.
- **Chef's Favourites** — up to four dishes marked `is_featured = True` in the database are pulled and displayed as menu cards with images, dietary badges, prices, and an Add to Cart button. Admins control which dishes appear here without any code changes.
- **Call-to-action banner** at the bottom of the page driving reservations.

---

### Menu

The menu page is the commercial heart of the site.

- **12 authentic Mediterranean items** across four categories: Starters, Mains, Desserts, Drinks. Every item has a realistic name, a detailed description, a price, and an estimated prep time.
- **Category filter tabs** — clicking a tab filters the grid to that category using a clean URL query string (`?category=starters`). The full view groups items under category headings with a styled divider.
- **Responsive card grid** built with CSS `grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))` — no framework grid classes. Cards have a hover lift effect and an image zoom on the thumbnail.
- **Dietary tag badges** — each menu item carries comma-separated tags (`vegetarian`, `vegan`, `gluten_free`, `spicy`, `dairy_free`). These are rendered as colour-coded pills on every card so customers can filter visually.
- **Per-item prep time** — each dish in the database stores how many minutes it takes to prepare (e.g. Greek Salad: 8 min, Grilled Lamb Chops: 35 min, Lemon Herb Chicken: 40 min). This feeds directly into the order ETA calculation.
- **Add to Cart** button on every card submits a POST form and increments the session cart without a page reload via a redirect-back pattern.
- **Image fallback** — if a menu item has no image uploaded, the card shows an emoji placeholder (`🍽️`) instead of a broken image.

---

### Session Cart

The cart requires no login — it lives entirely in the Django session.

- Items are stored as `{ "menu_item_id": quantity }` in `request.session['cart']`.
- The **navbar cart icon** shows a live badge with the total item count. This is injected globally via a context processor (`restaurant.context_processors.cart_count`) so the badge is accurate on every page.
- The **cart page** renders a full table with item name, unit price, a quantity input that auto-submits on change, a remove button, and a running subtotal.
- **Cart summary sidebar** shows subtotal and a Proceed to Checkout button.
- Quantity inputs use `onchange="this.form.submit()"` for a frictionless update experience with no JavaScript framework needed.

---

### Order System

Customers can place orders without creating an account.

- **Checkout page** collects name, email, phone (optional), and order type. The form adapts dynamically:
  - **Dine-in** → shows a party size field; delivery address is hidden.
  - **Takeaway** → shows a delivery address field; party size is hidden.
  - This is handled by a small inline JavaScript snippet that listens to the radio buttons and toggles field visibility.
- **Server-side price calculation** — the order total is computed from actual `MenuItem.price` values fetched from the database. The client never sends a price; even if someone tampers with the form, the total is always correct.
- `Order` and `OrderItem` models store a price snapshot (`unit_price`) at the time of ordering so historical totals remain accurate even if menu prices change later.
- On successful checkout, the cart is cleared, an `Order` + related `OrderItem` rows are saved, and the customer is redirected to the confirmation page.
- A **confirmation email** is sent (console backend in dev) with the full order summary and a link to the order tracker.

**Order statuses:** Pending → Preparing → Ready → Completed (or Cancelled at any point).

---

### Real-Time Order Tracker

This is the most technically interesting part of the site.

- Accessible at `/order-status/` — customers enter their order number and email (no login required).
- Once found, the tracker page renders with the order's current state and then **polls the server every 15 seconds** via a lightweight JSON API at `/order-status/<id>/api/?email=...`.
- **Countdown timer** — a `setInterval` loop ticks every second and displays a live `MM : SS` countdown to the ETA. The ETA is calculated as `order.created_at + max(prep_time_minutes across all items)` — modelling that a kitchen prepares dishes in parallel, not sequence.
- **Animated progress bar** fills from 0% to 100% as elapsed time moves toward the ETA. It transitions smoothly with CSS `transition: width 0.8s ease`.
- **4-step visual tracker** (Received → Preparing → Ready → Delivered) updates in real time as the kitchen staff change the order status from the dashboard. Each step dot shows a checkmark when passed and a pulsing ring on the active step.
- **Terminal states** — when the status reaches Completed or Cancelled, polling stops automatically, the live badge changes to a static indicator, and a green or red banner appears.
- **Per-item prep time display** — the items table shows each dish's estimated prep time as a `⏱ ~X min` badge so the customer understands why their ETA is what it is.
- The order confirmation page also shows the ETA immediately after checkout (e.g. "Ready in ~35 minutes (by 7:45 PM)") so customers know what to expect from the start.

---

###  Reservations

- Customers fill in name, email, phone, date/time, party size, optional notes, and optionally pre-order a menu item.
- The `item` field on the `Reservation` model is a nullable **ForeignKey to `MenuItem`** (not a plain text field), so pre-orders are properly linked and queryable.
- Reservation status flows through Pending → Confirmed → Cancelled, managed from the staff dashboard.
- Clicking "Order Now" on a menu card pre-fills the item dropdown in the reservation form via a URL query parameter (`?item=<id>`).

---

### 🎨 Custom CSS Design System

The entire visual layer is hand-written in `restaurant/static/css/style.css` — roughly 700 lines, zero dependencies.

**Colour palette** (inspired by Little Lemon's Mediterranean identity):
| Token | Hex | Use |
|---|---|---|
| `--color-primary` | `#F4CE14` | Lemon yellow — CTAs, accents, brand highlights |
| `--color-secondary` | `#495E57` | Sage green — headers, navbar, buttons |
| `--color-accent` | `#EE9972` | Coral — category labels, warm accents |
| `--color-bg` | `#EDEFEE` | Off-white — page backgrounds |
| `--color-text` | `#333333` | Charcoal — body text |

**Typography:** Georgia/serif for headings (warm, restaurant feel), Segoe UI/system-sans for body (clean, readable).

**Component library built from scratch:**
- Buttons (`.btn--primary`, `.btn--secondary`, `.btn--outline`, `.btn--danger`, size variants)
- Cards (menu cards with image zoom, feature cards, stat cards)
- Forms (custom label, input, focus ring, select arrow, radio group, error states)
- Navigation (sticky navbar with hamburger menu for mobile, active link indicator)
- Dietary tag badges (colour-coded per tag type)
- Status chips for orders and reservations
- Dashboard sidebar + data tables
- Hero section with overlay gradient
- Footer with three-column grid

**Responsive breakpoints:**
- `≤ 900px` — two-column layouts collapse, dashboard sidebar becomes a horizontal strip
- `≤ 640px` — navbar hamburger activates, menu grid goes single-column, hero stacks
- `≤ 400px` — stat cards go single-column, hero font scales down

---

### 🔐 Staff Dashboard

The custom dashboard at `/dashboard/` is separate from Django's built-in `/admin/` and designed for day-to-day restaurant operations.

- **Custom login page** at `/admin-login/` — branded page using Django's `authenticate()` and `login()` under the hood. Requires `is_staff=True`; regular users are rejected with an error message.
- **Overview page** shows three live stats for today: total orders, total reservations, revenue from completed orders. Below the stats are the 10 most recent orders and reservations.
- **Orders page** at `/dashboard/orders/` — full paginated table of all orders with inline status dropdowns. Staff can filter by status (Pending, Preparing, Ready, Completed, Cancelled) and by type (Dine-in / Takeaway). Status is updated with a single form submission without leaving the page.
- **Reservations page** at `/dashboard/reservations/` — same pattern, filter by status, inline confirm/cancel.
- **Django Admin** at `/admin/` is still fully available for managing `MenuItem`, `Category`, `BusinessHours`, and user accounts. The custom dashboard handles day-to-day ops; Admin handles configuration.
- All dashboard routes are protected by a `@staff_required` decorator that checks both `is_authenticated` and `is_staff`, redirecting to `/admin-login/` with a `?next=` parameter on failure.

---

### 📋 Data Models

#### `Category`
Organises menu items. Has `name`, `slug`, and `order` (controls display order on the menu page).

#### `MenuItem`
The core content model.
| Field | Type | Notes |
|---|---|---|
| `category` | FK → Category | Nullable; items without a category still display |
| `name` | CharField | |
| `description` | TextField | |
| `price` | DecimalField | Max 6 digits, 2 decimal places |
| `image` | ImageField | Stored in `media/menu_images/`; optional |
| `is_featured` | BooleanField | Controls appearance on home page |
| `dietary_tags` | CharField | Comma-separated: `vegetarian`, `vegan`, `gluten_free`, `spicy`, `dairy_free` |
| `prep_time_minutes` | PositiveSmallIntegerField | Used to calculate order ETA |

#### `Reservation`
| Field | Type | Notes |
|---|---|---|
| `name`, `email`, `contact` | Char/Email | Customer contact info |
| `time` | DateTimeField | Reservation date and time |
| `count` | IntegerField | Party size |
| `item` | FK → MenuItem | Nullable; optional dish pre-order |
| `status` | choices | Pending / Confirmed / Cancelled |

#### `Order`
| Field | Type | Notes |
|---|---|---|
| `customer_name`, `email`, `phone` | Char/Email | Contact details |
| `order_type` | choices | `dine_in` or `takeaway` |
| `delivery_address` | TextField | Required for takeaway |
| `party_size` | PositiveSmallInt | Required for dine-in |
| `status` | choices | Pending → Preparing → Ready → Completed / Cancelled |
| `total_price` | DecimalField | Set server-side at checkout; never from client |
| `created_at` | DateTimeField | Auto-set; used as ETA start time |

#### `OrderItem`
Links an `Order` to a `MenuItem` with a `quantity` and `unit_price` snapshot.

#### `BusinessHours`
One row per day of the week (0=Monday … 6=Sunday). Stores `open_time`, `close_time`, and `is_closed`. Used for the live "Open Now" indicator on the home and contact pages.

---

## Requirements

- Python 3.11+
- PostgreSQL 14+
- pip

---

## Setup & Installation

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd littlelemon
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create a PostgreSQL database

Open `psql` or pgAdmin and run:

```sql
CREATE DATABASE littlelemon;
CREATE USER littlelemon_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE littlelemon TO littlelemon_user;
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values. The minimum required fields are:

```
SECRET_KEY=<long-random-string>
DEBUG=True
DB_NAME=littlelemon
DB_USER=littlelemon_user
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```

The `.env` file is listed in `.gitignore` — never commit it.

### 5. Run migrations

```bash
python manage.py migrate
```

This creates all tables: Category, MenuItem, Reservation, Order, OrderItem, BusinessHours, plus Django's built-in auth/session tables.

### 6. Seed the menu

```bash
python manage.py seed_menu
```

This creates:
- **4 categories** — Starters, Mains, Desserts, Drinks
- **12 menu items** — each with description, price, dietary tags, prep time, and image path
- **7 days of business hours** — Mon–Thu 11am–10pm, Fri 11am–11pm, Sat–Sun 9am–11pm

Running it a second time is completely safe — it uses `get_or_create` so nothing is duplicated.

### 7. Create a superuser

```bash
python manage.py createsuperuser
```

Use these credentials to log in at:
- **Django Admin** → `http://127.0.0.1:8000/admin/`
- **Staff Dashboard** → `http://127.0.0.1:8000/admin-login/`

Superusers have `is_staff=True` automatically, which is what the dashboard checks.

### 8. Start the development server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

---

## Running Tests

```bash
python manage.py test restaurant
```

The test suite covers:

| Test | What it checks |
|---|---|
| `MenuViewTests` | Menu page returns 200, all items appear, category filter excludes other categories |
| `ReservationFormTests` | Reservation page loads, valid submission creates a record and redirects, invalid submission re-renders with errors |
| `OrderCreationTests` | Checkout with empty cart redirects, dine-in order saves with correct total, takeaway without address fails validation, takeaway with address saves correctly |
| `DashboardAuthTests` | Unauthenticated users are redirected to `/admin-login/`, non-staff users are rejected, staff users can access all dashboard pages |
| `OrderStatusTests` | Status page loads, correct order+email lookup returns the order, wrong email returns nothing |

---

## Image Assets

All images are bundled — downloaded from Unsplash at project build time.

### Site images — `restaurant/static/images/`

| Filename | Page | Description |
|---|---|---|
| `restaurantt.jpg` | Home hero | Warm restaurant food spread |
| `aboutt.jpg` | About | Cozy restaurant dining room |
| `contact.jpg` | Contact | Restaurant exterior / street scene |

### Menu images — `media/menu_images/`

| Filename | Dish | Prep time |
|---|---|---|
| `greek-salad.jpg` | Greek Salad | 8 min |
| `bruschetta.jpg` | Bruschetta | 10 min |
| `hummus-plate.jpg` | Hummus Plate | 5 min |
| `vine-leaves.jpg` | Stuffed Vine Leaves | 12 min |
| `lamb-chops.jpg` | Grilled Lamb Chops | 35 min |
| `lemon-chicken.jpg` | Lemon Herb Chicken | 40 min |
| `falafel-wrap.jpg` | Falafel Wrap | 15 min |
| `seafood-pasta.jpg` | Seafood Pasta | 25 min |
| `baklava.jpg` | Baklava | 5 min |
| `lemon-tart.jpg` | Lemon Tart | 8 min |
| `lemonade.jpg` | Mediterranean Lemonade | 5 min |
| `mint-tea.jpg` | Moroccan Mint Tea | 5 min |

To add or replace images, upload through Django Admin → Menu Items, or drop files directly into `media/menu_images/`. Cards fall back to a `🍽️` emoji if no image is set.

---

## URL Reference

### Public pages

| URL | Name | Description |
|---|---|---|
| `/` | `home` | Home page — hero, featured dishes, CTA |
| `/menu/` | `menu` | Full menu, filterable by `?category=<slug>` |
| `/about/` | `about` | About page with story and values |
| `/contact/` | `contact` | Address, phone, email, live opening hours |
| `/reservation/` | `reservation` | Table booking form |

### Cart & orders

| URL | Name | Description |
|---|---|---|
| `/cart/` | `cart_view` | Shopping cart — review, update quantities, remove |
| `/cart/add/<id>/` | `cart_add` | POST — add 1 of item to cart |
| `/cart/remove/<id>/` | `cart_remove` | POST — remove item entirely from cart |
| `/cart/update/<id>/` | `cart_update` | POST — set exact quantity (0 removes) |
| `/checkout/` | `checkout` | Checkout form — name, email, dine-in or takeaway |
| `/order-confirmation/<id>/` | `order_confirmation` | Post-checkout summary with ETA |
| `/order-status/` | `order_status` | Live order tracker — lookup by order # + email |
| `/order-status/<id>/api/` | `order_status_api` | JSON endpoint polled by the live tracker |

### Staff

| URL | Name | Description |
|---|---|---|
| `/admin-login/` | `admin_login` | Custom branded staff login page |
| `/dashboard/` | `dashboard` | Overview — today's stats, recent orders & reservations |
| `/dashboard/orders/` | `dashboard_orders` | All orders, filterable, inline status update |
| `/dashboard/reservations/` | `dashboard_reservations` | All reservations, filterable, inline status update |
| `/dashboard/orders/<id>/status/` | `update_order_status` | POST — update a single order's status |
| `/dashboard/reservations/<id>/status/` | `update_reservation_status` | POST — update a single reservation's status |
| `/dashboard/logout/` | `dashboard_logout` | Log out and redirect to login page |
| `/admin/` | — | Django Admin — menu, categories, business hours |

---

## Environment Variables

All sensitive config lives in `.env` (git-ignored). Copy `.env.example` to get started.

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | Django secret key — use a long random string in production |
| `DEBUG` | `False` | Set to `True` for local development |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated list of allowed hosts |
| `DB_NAME` | `littlelemon` | PostgreSQL database name |
| `DB_USER` | `postgres` | PostgreSQL username |
| `DB_PASSWORD` | — | PostgreSQL password |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `EMAIL_BACKEND` | `console` backend | Set to SMTP backend for real emails |
| `DEFAULT_FROM_EMAIL` | `noreply@littlelemon.com` | Sender address for order confirmations |

---

## Email Configuration

By default the project uses Django's console email backend — confirmation emails are printed to the terminal running `runserver`. This is intentional for local development: you can see exactly what the customer would receive without needing an email account.

**To switch to real email (e.g. Gmail SMTP), add these to `.env`:**

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=you@gmail.com
```

Customers receive an order confirmation email on checkout containing their order number, itemised summary, total, order type, and a direct link to the live order tracker.
