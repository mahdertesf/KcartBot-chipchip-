import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta
from constants import PRODUCT_ENHANCEMENTS

DATA_DIR = os.path.join(os.path.dirname(__file__), '../../', 'data')
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "competitor_prices.csv")


DAYS_OF_HISTORY = 365
SEASONALITY_INTENSITY = 0.3
NOISE_INTENSITY = 0.02
COMPETITOR_TIERS = {
    "local_shop": 1.0,
    "supermarket": 1.30,
    "distribution_center": 0.85
}

def run_historical_data_pipeline():
    """
    Orchestrates the pipeline to generate historical competitor prices.
    It enhances product data in-memory for the simulation, ensuring the
    original product data file on disk remains unchanged.
    """
    print("--- Starting Historical Data Generation Pipeline ---")

    try:
        products_df = pd.read_csv(PRODUCTS_FILE)
    except FileNotFoundError:
        print(f"Error: The file '{PRODUCTS_FILE}' was not found. Please run generate_products.py first.")
        return

    print("\n[STEP 1/2] Enhancing product data in memory for simulation...")
    
    def get_base_price(internal_name):
        return PRODUCT_ENHANCEMENTS.get(internal_name, {}).get("price", 0.0)

    def get_peak_month(internal_name):
        return PRODUCT_ENHANCEMENTS.get(internal_name, {}).get("peak_month", 1)

    enhanced_products_df = products_df.copy()
    enhanced_products_df['base_price_etb'] = enhanced_products_df['internal_name'].apply(get_base_price)
    enhanced_products_df['season_peak_month'] = enhanced_products_df['internal_name'].apply(get_peak_month)
    print("In-memory data enhancement complete.")

    print("\n[STEP 2/2] Generating 1-year of historical competitor prices...")
    
    prices_data = []
    today = datetime.now()

    print(f"Simulating prices for {len(enhanced_products_df)} products over {DAYS_OF_HISTORY} days...")

    for index, product in enhanced_products_df.iterrows():
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
            print(f"  ...processed {index + 1}/{len(enhanced_products_df)} products...")

    prices_df = pd.DataFrame(prices_data)
    prices_df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"Successfully generated {len(prices_df)} historical price records.")
    print(f"Data saved to '{OUTPUT_FILE}'")
    
    print("\n--- Historical Data Generation Pipeline Complete ---")

if __name__ == "__main__":
    run_historical_data_pipeline()