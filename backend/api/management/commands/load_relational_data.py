import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from api.models import User, Product, Inventory, Order, OrderItem, CompetitorPrice


DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.csv')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products.csv')
INVENTORY_FILE = os.path.join(DATA_DIR, 'inventory.csv')
ORDERS_FILE = os.path.join(DATA_DIR, 'orders.csv')
ORDER_ITEMS_FILE = os.path.join(DATA_DIR, 'order_items.csv')
COMPETITOR_PRICES_FILE = os.path.join(DATA_DIR, 'competitor_prices.csv')

class Command(BaseCommand):
    help = 'Loads all synthetic data from CSV files into the database'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('--- Starting Data Loading Process ---'))
        
        # Clear existing data
        self.stdout.write('Clearing existing data...')
        CompetitorPrice.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Inventory.objects.all().delete()
        Product.objects.all().delete()
        User.objects.all().delete()
        
        self.load_users()
        self.load_products()
        self.load_inventory()
        self.load_orders()
        self.load_order_items()
        self.load_competitor_prices()
        
        self.stdout.write(self.style.SUCCESS('--- Data Loading Complete ---'))

    def load_users(self):
        self.stdout.write('Loading Users...')
        df = pd.read_csv(USERS_FILE)
        for index, row in df.iterrows():
            User.objects.create(
                id=row['user_id'],
                name=row['name'],
                phone_number=row['phone_number'],
                default_location=row['default_location'],
                role=row['role'],
                created_date=row['created_date']
            )
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(df)} users.'))

    def load_products(self):
        self.stdout.write('Loading Products...')
        df = pd.read_csv(PRODUCTS_FILE)
        for index, row in df.iterrows():
            Product.objects.create(
                product_id=row['product_id'],
                product_name=row['product_name'],
                internal_name=row['internal_name'],
                unit=row['unit'],
                photo_url=row['photo_url'] if pd.notna(row['photo_url']) else ''
            )
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(df)} products.'))

    def load_inventory(self):
        self.stdout.write('Loading Inventory...')
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
                self.stdout.write(self.style.WARNING(f"Skipping duplicate inventory entry for supplier {row['supplier_id']} and product {row['product_id']}"))
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(df)} inventory items.'))

    def load_orders(self):
        self.stdout.write('Loading Orders...')
        df = pd.read_csv(ORDERS_FILE)
        loaded_count = 0
        for index, row in df.iterrows():
            try:
                Order.objects.create(
                    order_id=row['order_id'],
                    user_id=row['user_id'],
                    order_date=row['order_date'],
                    status=row['status']
                )
                loaded_count += 1
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING(f"Skipping order {row['order_id']} due to foreign key constraint: {e}"))
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {loaded_count} orders.'))
        
    def load_order_items(self):
        self.stdout.write('Loading Order Items...')
        df = pd.read_csv(ORDER_ITEMS_FILE)
        items_to_create = []
        for index, row in df.iterrows():
            try:
                items_to_create.append(
                    OrderItem(
                        order_item_id=row['order_item_id'],
                        order_id=row['order_id'],
                        product_id=row['product_id'],
                        quantity=row['quantity'],
                        price_per_unit_etb=row['price_per_unit_etb']
                    )
                )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Skipping order item {row['order_item_id']} due to error: {e}"))
        
        try:
            OrderItem.objects.bulk_create(items_to_create, batch_size=500, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(items_to_create)} order items.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error bulk creating order items: {e}'))

    def load_competitor_prices(self):
        self.stdout.write('Loading Competitor Prices...')
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
        CompetitorPrice.objects.bulk_create(prices_to_create, batch_size=500)
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(df)} competitor prices.'))