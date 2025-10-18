import pandas as pd
import random
import os
import uuid
from datetime import datetime, timedelta

USERS_FILE = os.path.join("../../data", "users.csv")
PRODUCTS_FILE = os.path.join("../../data", "products.csv")
COMPETITOR_PRICES_FILE = os.path.join("../../data", "competitor_prices.csv")
OUTPUT_DIR = "../../data"
ORDERS_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "orders.csv")
ORDER_ITEMS_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "order_items.csv")

DAYS_OF_HISTORY = 365
AVG_ORDERS_PER_DAY = 50
MAX_ITEMS_PER_ORDER = 5

def generate_transaction_data():
    """
    Generates a 1-year historical dataset of orders and their corresponding items.
    Simulates price elasticity where lower prices lead to higher quantity sales.
    """
    print("Starting historical transaction data generation...")

    try:
        users_df = pd.read_csv(USERS_FILE)
        products_df = pd.read_csv(PRODUCTS_FILE)
        competitor_prices_df = pd.read_csv(COMPETITOR_PRICES_FILE)
    except FileNotFoundError as e:
        print(f"Error: Prerequisite file not found: {e.filename}")
        print("Please ensure all previous generation scripts have been run.")
        return

    customers = users_df[users_df['role'] == 'customer']['user_id'].tolist()
    if not customers:
        print("Error: No customers found in users.csv.")
        return
        
    product_base_prices = products_df.set_index('product_id')['base_price_etb'].to_dict()
    all_product_ids = products_df['product_id'].tolist()

    competitor_prices_df.set_index(['date', 'product_id'], inplace=True)
    competitor_prices_df.sort_index(inplace=True)

    orders_data = []
    order_items_data = []
    today = datetime.now().date()

    print(f"Simulating transactions for {DAYS_OF_HISTORY} days...")

    for i in range(DAYS_OF_HISTORY):
        current_date = today - timedelta(days=i)
        current_date_str = current_date.strftime("%Y-%m-%d")
        
        num_orders_today = random.randint(int(AVG_ORDERS_PER_DAY * 0.5), int(AVG_ORDERS_PER_DAY * 1.5))

        for _ in range(num_orders_today):
            order_id = str(uuid.uuid4())
            order_datetime = datetime.combine(current_date, datetime.min.time()) + timedelta(seconds=random.randint(0, 86399))
            
            orders_data.append({
                "order_id": order_id,
                "user_id": random.choice(customers),
                "order_date": order_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "completed"
            })

            num_items_in_order = random.randint(1, MAX_ITEMS_PER_ORDER)
            products_in_order = random.sample(all_product_ids, num_items_in_order)

            for product_id in products_in_order:
                try:
                    kcart_price_today = competitor_prices_df.loc[(current_date_str, product_id)]
                    kcart_price_today = kcart_price_today[kcart_price_today['competitor_tier'] == 'local_shop']['price_per_unit_etb'].iloc[0]
                except (KeyError, IndexError):
                    continue

                base_price = product_base_prices.get(product_id, kcart_price_today)

                if kcart_price_today < base_price * 0.9:
                    quantity = round(random.uniform(2.0, 10.0), 2)
                elif kcart_price_today > base_price * 1.1:
                    quantity = round(random.uniform(0.5, 2.0), 2)
                else:
                    quantity = round(random.uniform(1.0, 5.0), 2)
                
                order_items_data.append({
                    "order_item_id": str(uuid.uuid4()),
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "price_per_unit_etb": kcart_price_today
                })

    orders_df = pd.DataFrame(orders_data)
    order_items_df = pd.DataFrame(order_items_data)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    orders_df.to_csv(ORDERS_OUTPUT_FILE, index=False)
    order_items_df.to_csv(ORDER_ITEMS_OUTPUT_FILE, index=False)

    print("-" * 30)
    print(f"Successfully generated {len(orders_df)} orders and {len(order_items_df)} order items.")
    print(f"Data saved to '{ORDERS_OUTPUT_FILE}' and '{ORDER_ITEMS_OUTPUT_FILE}'")
    print("-" * 30)

    print("Sample of generated orders data:")
    print(orders_df.head())
    print("\nSample of generated order items data:")
    print(order_items_df.head())


if __name__ == "__main__":
    generate_transaction_data()