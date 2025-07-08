import os
import pandas as pd
from pymongo import MongoClient
import re
from dotenv import load_dotenv
load_dotenv()
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# uri = os.getenv("URI_MONGO")

# client = MongoClient(uri, server_api=ServerApi('1'))
# csv_folder = "csv-database"
# db = client["LaLiga"]  

# # Loop over all CSV files in the folder
# season_pattern = re.compile(r"la_liga_schedule_(\d{4}_\d{2})_new\.csv$")  
# print(f"Processing CSV files in folder: {csv_folder}")
# print(f"Using MongoDB database: {db.name}")
# print(f"Season pattern: {season_pattern.pattern}")

# for filename in os.listdir(csv_folder):
#     if filename.endswith(".csv"):
#         match = season_pattern.search(filename)
#         print(f"Found file: {filename}")
#         if match:
#             season = match.group(1)  
#             collection = db[season]  
#             file_path = os.path.join(csv_folder, filename)

#             df = pd.read_csv(file_path)
#             collection.insert_many(df.to_dict("records"))
#             print(f"✅ Uploaded {len(df)} matches to LaLiga.{season}")
#         else:
#             print(f"❌ Filename doesn't match expected pattern: {filename}")

uri = os.getenv("URI_MONGO")

# Connect to MongoDB
client = MongoClient(uri, server_api=ServerApi('1'))
csv_folder = "csv-database"
db = client["EPL"]  # Use "EPL" as the database name

# Regex pattern for EPL CSV files
epl_pattern = re.compile(r"epl_schedule_(\d{4}_\d{4})\.csv$")  # Matches files like "epl_schedule_2024_2025.csv"
print(f"Processing CSV files in folder: {csv_folder}")
print(f"Using MongoDB database: {db.name}")
print(f"EPL pattern: {epl_pattern.pattern}")

# Loop over all CSV files in the folder
for filename in os.listdir(csv_folder):
    if filename.endswith(".csv"):
        match = epl_pattern.search(filename)
        print(f"Found file: {filename}")
        if match:
            season = match.group(1)  # Extract the season (e.g., "2024_2025")
            collection = db[season]  # Use the season as the collection name
            file_path = os.path.join(csv_folder, filename)

            # Read the CSV file
            df = pd.read_csv(file_path)

            # Ensure numeric fields are properly converted
            df["home_xg"] = pd.to_numeric(df["home_xg"], errors="coerce")
            df["away_xg"] = pd.to_numeric(df["away_xg"], errors="coerce")

            # Insert data into MongoDB
            collection.insert_many(df.to_dict("records"))
            print(f"✅ Uploaded {len(df)} matches to EPL.{season}")
        else:
            print(f"❌ Filename doesn't match expected pattern: {filename}")