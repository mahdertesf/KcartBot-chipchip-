import pandas as pd
import random
import os
import uuid
from datetime import datetime, timedelta

USERS_FILE = os.path.join("../../data", "users.csv")
PRODUCTS_FILE = os.path.join("../../data", "products.csv")
COMPETITOR_PRICES_FILE = os.path.join("../../data", "competitor_prices.csv")
OUTPUT_DIR = "../../data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "inventory.csv")

MIN_PRODUCTS_PER_SUPPLIER = 3
MAX_PRODUCTS_PER_SUPPLIER = 20

def generate_inventory_data():
    """
    Generates a synthetic dataset of inventory listings with realistic pricing.
    It links suppliers from users.csv with products from products.csv and uses
    competitor_prices.csv to set a believable current price.
    """
    print("Starting inventory data generation with realistic pricing...")

    try:
        users_df = pd.read_csv(USERS_FILE)
        products_df = pd.read_csv(PRODUCTS_FILE)
        competitor_prices_df = pd.read_csv(COMPETITOR_PRICES_FILE)
    except FileNotFoundError as e:
        print(f"Error: Prerequisite file not found: {e.filename}")
        print("Please ensure all previous generation scripts have been run.")
        return

    print("Analyzing today's market prices from historical data...")
    latest_date = competitor_prices_df['date'].max()
    todays_prices_df = competitor_prices_df[competitor_prices_df['date'] == latest_date]
    
    todays_market = todays_prices_df.pivot(
        index='product_id', 
        columns='competitor_tier', 
        values='price_per_unit_etb'
    ).rename(columns={'local_shop': 'min_price', 'supermarket': 'max_price'})

    suppliers = users_df[users_df['role'] == 'supplier']
    if suppliers.empty:
        print("Error: No suppliers found in users.csv.")
        return

    supplier_ids = suppliers['user_id'].tolist()
    product_ids = products_df['product_id'].tolist()

    inventory_data = []

    print(f"Generating inventory for {len(supplier_ids)} suppliers...")
    for supplier_id in supplier_ids:
        num_products_for_supplier = random.randint(MIN_PRODUCTS_PER_SUPPLIER, MAX_PRODUCTS_PER_SUPPLIER)
        products_to_add = random.sample(product_ids, num_products_for_supplier)

        for product_id in products_to_add:
            available_date = datetime.now() - timedelta(days=random.randint(1, 30))
            expiry_date = available_date + timedelta(days=random.randint(7, 90))

            try:
                market_info = todays_market.loc[product_id]
                min_price = market_info['min_price']
                max_price = market_info['max_price']
                realistic_price = round(random.uniform(min_price * 1.05, max_price * 0.95), 2)
            except KeyError:
                realistic_price = round(random.uniform(30.00, 300.00), 2)

            inventory_item = {
                "inventory_id": str(uuid.uuid4()),
                "supplier_id": supplier_id,
                "product_id": product_id,
                "quantity_available": round(random.uniform(20.0, 500.0), 2),
                "price_per_unit_etb": realistic_price,
                "status": "active",
                "available_date": available_date.strftime("%Y-%m-%d"),
                "expiry_date": expiry_date.strftime("%Y-%m-%d")
            }
            inventory_data.append(inventory_item)

    inventory_df = pd.DataFrame(inventory_data)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    inventory_df.to_csv(OUTPUT_FILE, index=False)

    print("-" * 30)
    print(f"Successfully generated {len(inventory_df)} inventory listings with realistic prices.")
    print(f"Data saved to '{OUTPUT_FILE}'")
    print("-" * 30)

    print("Sample of generated inventory data:")
    print(inventory_df.head())

if __name__ == "__main__":
    generate_inventory_data()