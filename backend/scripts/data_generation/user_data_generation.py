import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta
import os
import uuid
from constants import LOCATIONS, Names

NUM_CUSTOMERS = 300
NUM_SUPPLIERS = 70
OUTPUT_DIR = "../data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "users.csv")


def generate_user_data():
    """
    Generates a synthetic dataset of users (customers and suppliers)
    with an expanded list of regional locations and saves it to a CSV file.
    """
    print("Starting user data generation with expanded locations...")

    fake = Faker()
    users_data = []

    print(f"Generating {NUM_CUSTOMERS} customers...")
    for _ in range(NUM_CUSTOMERS):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        created_date = fake.date_between(start_date=start_date, end_date=end_date)

        user = {
            "user_id": str(uuid.uuid4()),
            "name": random.choice(Names),
            "phone_number": f"+2519{fake.random_int(min=10000000, max=99999999)}",
            "default_location": random.choice(LOCATIONS),
            "role": "customer",
            "created_date": created_date
        }
        users_data.append(user)

    print(f"Generating {NUM_SUPPLIERS} suppliers...")
    for _ in range(NUM_SUPPLIERS):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        created_date = fake.date_between(start_date=start_date, end_date=end_date)

        user = {
            "user_id": str(uuid.uuid4()),
            "name": random.choice(Names),
            "phone_number": f"+2519{fake.random_int(min=10000000, max=99999999)}",
            "default_location": random.choice(LOCATIONS),
            "role": "supplier",
            "created_date": created_date
        }
        users_data.append(user)

    users_df = pd.DataFrame(users_data)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    users_df.to_csv(OUTPUT_FILE, index=False)
    
    print("-" * 30)
    print(f"Successfully generated {len(users_df)} users.")
    print(f"Data saved to '{OUTPUT_FILE}'")
    print("-" * 30)

    print("Sample of generated data:")
    print(users_df.head())
    print("...")
    print(users_df.tail())


if __name__ == "__main__":
    generate_user_data()
    
