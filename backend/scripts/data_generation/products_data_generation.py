import pandas as pd
import os
import uuid  
from constants import PRODUCTS_CATALOG



OUTPUT_DIR = "../../data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "products.csv")

def generate_product_catalog():
    """
    Generates the master catalog of unique products available on the platform,
    using UUIDs for product IDs.
    """
    print("Starting master product catalog generation with UUIDs...")

    products_data = []

    for display_name, simple_name in PRODUCTS_CATALOG.items():
        if simple_name in ["milk", "yogurt"]:
            unit = "Liter"
        else:
            unit = "Kg"

        product = {
            "product_id": str(uuid.uuid4()),
            "product_name": display_name,
            "internal_name": simple_name,
            "unit": unit,
            "photo_url": "" 
        }
        products_data.append(product)

    products_df = pd.DataFrame(products_data)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    products_df.to_csv(OUTPUT_FILE, index=False)

    print("-" * 30)
    print(f"Successfully generated master catalog with {len(products_df)} products.")
    print(f"Data saved to '{OUTPUT_FILE}'")
    print("-" * 30)
    
    print("Generated product catalog with UUIDs:")
    print(products_df.to_string())

if __name__ == "__main__":
    generate_product_catalog()