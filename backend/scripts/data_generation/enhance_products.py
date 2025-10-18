import pandas as pd
import os
from constants import PRODUCT_ENHANCEMENTS


PRODUCTS_FILE = os.path.join("../../data", "products.csv")


def enhance_product_data():
    """
    Reads the existing products.csv file, adds base_price and season_peak_month
    columns, and overwrites the file with the new data.
    """
    print(f"Starting to enhance '{PRODUCTS_FILE}'...")

    try:
        products_df = pd.read_csv(PRODUCTS_FILE)
    except FileNotFoundError:
        print(f"Error: The file '{PRODUCTS_FILE}' was not found.")
        print("Please run generate_products.py first.")
        return
    
    def get_base_price(internal_name):
        return PRODUCT_ENHANCEMENTS.get(internal_name, {}).get("price", 0.0)

    def get_peak_month(internal_name):
        return PRODUCT_ENHANCEMENTS.get(internal_name, {}).get("peak_month", 1)

    print("Adding 'base_price_etb' and 'season_peak_month' columns...")
    products_df['base_price_etb'] = products_df['internal_name'].apply(get_base_price)
    products_df['season_peak_month'] = products_df['internal_name'].apply(get_peak_month)

    products_df.to_csv(PRODUCTS_FILE, index=False)

    print("-" * 30)
    print(f"Successfully enhanced '{PRODUCTS_FILE}'.")
    print("The file has been updated with the new columns.")
    print("-" * 30)

    print("Updated product catalog:")
    print(products_df.to_string())

if __name__ == "__main__":
    enhance_product_data()