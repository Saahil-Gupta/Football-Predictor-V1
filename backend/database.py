import os
import pandas as pd
from pymongo import MongoClient
import re
from dotenv import load_dotenv
load_dotenv()
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = os.getenv("URI_MONGO")

client = MongoClient(uri, server_api=ServerApi('1'))
csv_folder = "csv-database"
db = client["LaLiga"]  

# Loop over all CSV files in the folder
season_pattern = re.compile(r"la_liga_schedule_(\d{4}_\d{2})_new\.csv$")  # Matches 'la_liga_schedule_2020_21_new.csv'
print(f"Processing CSV files in folder: {csv_folder}")
print(f"Using MongoDB database: {db.name}")
print(f"Season pattern: {season_pattern.pattern}")

for filename in os.listdir(csv_folder):
    if filename.endswith(".csv"):
        match = season_pattern.search(filename)
        print(f"Found file: {filename}")
        if match:
            season = match.group(1)  # e.g., '2020_21'
            collection = db[season]  # use as collection name
            file_path = os.path.join(csv_folder, filename)

            df = pd.read_csv(file_path)
            # Insert to MongoDB
            collection.insert_many(df.to_dict("records"))
            print(f"✅ Uploaded {len(df)} matches to LaLiga.{season}")
        else:
            print(f"❌ Filename doesn't match expected pattern: {filename}")

