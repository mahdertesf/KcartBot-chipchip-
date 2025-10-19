import os
import sys
import django
import pandas as pd
from django.db import transaction, IntegrityError

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import User, Product, Inventory, Order, OrderItem, CompetitorPrice

DATA_DIR = os.path.join(backend_dir, 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.csv')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products.csv')
INVENTORY_FILE = os.path.join(DATA_DIR, 'inventory.csv')
ORDERS_FILE = os.path.join(DATA_DIR, 'orders.csv')
ORDER_ITEMS_FILE = os.path.join(DATA_DIR, 'order_items.csv')
COMPETITOR_PRICES_FILE = os.path.join(DATA_DIR, 'competitor_prices.csv')

def print_success(message):
    print(f"[SUCCESS] {message}")

def print_warning(message):
    print(f"[WARNING] {message}")

def print_info(message):
    print(f"[INFO] {message}")

@transaction.atomic
def load_all_data():
    print_success("--- Starting Data Loading Process ---")
    
    print_info("Clearing existing data...")
    OrderItem.objects.all().delete()
    Order.objects.all().delete()
    Inventory.objects.all().delete()
    CompetitorPrice.objects.all().delete()
    Product.objects.all().delete()
    User.objects.all().delete()
    print_success("Existing data cleared.")

    load_users()
    load_products()
    load_inventory()
    load_orders()
    load_order_items()
    load_competitor_prices()
    
    print_success("--- Data Loading Complete ---")

def load_users():
    print_info("Loading Users for Django Auth System...")
    df = pd.read_csv(USERS_FILE)
    
    for index, row in df.iterrows():
        base_username = row['name'].lower().replace(' ', '_').replace('.', '')
        username = f"{base_username}_{row['user_id']}"

        name_parts = row['name'].split(' ')
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

        user = User(
            id=row['user_id'],
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone_number=row['phone_number'],
            default_location=row['default_location'],
            role=row['role'],
            is_staff=False,
            is_superuser=False,
        )
        user.set_password("password123")
        user.save()

        User.objects.filter(id=row['user_id']).update(date_joined=row['created_date'])

    print_success(f'Successfully loaded and adapted {len(df)} users for Django Auth.')

def load_products():
    print_info("Loading Products...")
    df = pd.read_csv(PRODUCTS_FILE)
    for index, row in df.iterrows():
        Product.objects.create(
            product_id=row['product_id'],
            product_name=row['product_name'],
            internal_name=row['internal_name'],
            unit=row['unit'],
            photo_url=row['photo_url'] if pd.notna(row['photo_url']) else ''
        )
    print_success(f'Successfully loaded {len(df)} products.')

def load_inventory():
    print_info("Loading Inventory...")
    df = pd.read_csv(INVENTORY_FILE)
    for index, row in df.iterrows():
        try:
            Inventory.objects.create(
                inventory_id=row['inventory_id'],
                supplier_id=row['supplier_id'],
                product_id=row['product_id'],
                quantity_available=row['quantity_available'],
                price_per_unit_etb=row['price_per_unit_etb'],
                status=row['status'],
                available_date=row['available_date'],
                expiry_date=row['expiry_date'] if pd.notna(row['expiry_date']) else None
            )
        except IntegrityError:
            print_warning(f"Skipping duplicate inventory for supplier {row['supplier_id']} and product {row['product_id']}")
    print_success(f'Successfully loaded {len(df)} inventory items.')

def load_orders():
    print_info("Loading Orders...")
    df = pd.read_csv(ORDERS_FILE)
    orders_to_create = []
    for index, row in df.iterrows():
        orders_to_create.append(
            Order(
                order_id=row['order_id'],
                user_id=row['user_id'],
                order_date=row['order_date'],
                status=row['status']
            )
        )
    Order.objects.bulk_create(orders_to_create, batch_size=500, ignore_conflicts=True)
    print_success(f'Successfully loaded {len(df)} orders.')
    
def load_order_items():
    print_info("Loading Order Items...")
    df = pd.read_csv(ORDER_ITEMS_FILE)
    items_to_create = []
    for index, row in df.iterrows():
        items_to_create.append(
            OrderItem(
                order_item_id=row['order_item_id'],
                order_id=row['order_id'],
                product_id=row['product_id'],
                quantity=row['quantity'],
                price_per_unit_etb=row['price_per_unit_etb']
            )
        )
    OrderItem.objects.bulk_create(items_to_create, batch_size=500, ignore_conflicts=True)
    print_success(f'Successfully loaded {len(df)} order items.')

def load_competitor_prices():
    print_info("Loading Competitor Prices...")
    df = pd.read_csv(COMPETITOR_PRICES_FILE)
    prices_to_create = []
    for index, row in df.iterrows():
        prices_to_create.append(
            CompetitorPrice(
                product_id=row['product_id'],
                date=row['date'],
                competitor_tier=row['competitor_tier'],
                price_per_unit_etb=row['price_per_unit_etb']
            )
        )
    CompetitorPrice.objects.bulk_create(prices_to_create, batch_size=500, ignore_conflicts=True)
    print_success(f'Successfully loaded {len(df)} competitor prices.')

if __name__ == "__main__":
    try:
        load_all_data()
    except Exception as e:
        print(f"[ERROR] Error loading data: {e}")
        sys.exit(1)