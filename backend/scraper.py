from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

URL = "https://fbref.com/en/comps/12/La-Liga-Stats"

# Setup Selenium
options = Options()
# comment this line to show the browser
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(URL)

# Wait for table to load
WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "table.stats_table"))
)

# Extract match rows
rows = driver.find_elements(By.CSS_SELECTOR, "table.stats_table tbody tr")

data = []

for row in rows:
    try:
        if "thead" in row.get_attribute("class"):
            continue

        team = row.find_element(By.CSS_SELECTOR, "[data-stat='team']").text
        # date = row.find_element(By.CSS_SELECTOR, "[data-stat='date']").text
        # home_team = row.find_element(By.CSS_SELECTOR, "[data-stat='home_team']").text
        # away_team = row.find_element(By.CSS_SELECTOR, "[data-stat='away_team']").text
        # home_xg = row.find_element(By.CSS_SELECTOR, "[data-stat='home_xg']").text
        # away_xg = row.find_element(By.CSS_SELECTOR, "[data-stat='away_xg']").text
        # score = row.find_element(By.CSS_SELECTOR, "[data-stat='score']").text

        # if not score or score == "":  # skip unplayed matches
        #     continue

        data.append({
            "team": team
            # "date": date,
            # "home_team": home_team,
            # "away_team": away_team,
            # "home_xg": home_xg,
            # "away_xg": away_xg,
            # "score": score
        })

    except Exception as e:
        continue

driver.quit()

# Save to CSV
df = pd.DataFrame(data)
df.to_csv("la_liga_schedule_2014_25_new.csv", index=False)
print(f"✅ Scraped {len(df)} played matches.")