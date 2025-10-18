import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta

PRODUCTS_FILE = os.path.join("../../data", "products.csv")
OUTPUT_DIR = "../../data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "competitor_prices.csv")

DAYS_OF_HISTORY = 365
SEASONALITY_INTENSITY = 0.3
NOISE_INTENSITY = 0.02

COMPETITOR_TIERS = {
    "local_shop": 1.0,
    "supermarket": 1.30,
    "distribution_center": 0.85
}

def generate_competitor_prices():
    """
    Generates a 1-year historical dataset of competitor prices for all products.
    Uses a sine wave to simulate seasonality and adds daily noise for realism.
    """
    print("Starting historical competitor price generation...")

    try:
        products_df = pd.read_csv(PRODUCTS_FILE)
    except FileNotFoundError:
        print(f"Error: The file '{PRODUCTS_FILE}' was not found.")
        print("Please run generate_products.py and enhance_products.py first.")
        return

    prices_data = []
    today = datetime.now()

    print(f"Simulating prices for {len(products_df)} products over {DAYS_OF_HISTORY} days...")

    for index, product in products_df.iterrows():
        base_price = product['base_price_etb']
        peak_month = product['season_peak_month']
        peak_day_of_year = peak_month * 30 - 15

        for i in range(DAYS_OF_HISTORY):
            current_date = today - timedelta(days=i)
            day_of_year = current_date.timetuple().tm_yday

            sine_value = np.sin(2 * np.pi * (day_of_year - peak_day_of_year) / 365)
            seasonality_factor = 1 + (SEASONALITY_INTENSITY * sine_value)
            noise_factor = random.uniform(1 - NOISE_INTENSITY, 1 + NOISE_INTENSITY)
            daily_base_price = base_price * seasonality_factor * noise_factor

            for tier, markup in COMPETITOR_TIERS.items():
                final_price = round(daily_base_price * markup, 2)
                prices_data.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "product_id": product['product_id'],
                    "competitor_tier": tier,
                    "price_per_unit_etb": final_price
                })
        
        if (index + 1) % 5 == 0:
            print(f"  ...processed {index + 1}/{len(products_df)} products...")

    prices_df = pd.DataFrame(prices_data)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    prices_df.to_csv(OUTPUT_FILE, index=False)

    print("-" * 30)
    print(f"Successfully generated {len(prices_df)} historical price records.")
    print(f"Data saved to '{OUTPUT_FILE}'")
    print("-" * 30)

    print("Sample of generated competitor price data:")
    print(prices_df.head())
    print("...")
    print(prices_df.tail())

if __name__ == "__main__":
    generate_competitor_prices()