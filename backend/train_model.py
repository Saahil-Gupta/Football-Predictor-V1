import pandas as pd
from pymongo import MongoClient
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import joblib
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
uri = os.getenv("URI_MONGO")
client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)
db = client["LaLiga"]

# Load all season collections
season_keys = [
    "2017_18", "2018_19", "2019_20", "2020_21",
    "2021_22", "2022_23", "2023_24", "2024_25"
]

all_dfs = []
for season in season_keys:
    collection = db[season]
    data = list(collection.find({}, {'_id': 0}))
    if data:
        df = pd.DataFrame(data)
        df["season"] = season
        all_dfs.append(df)

# Combine all seasons into a single DataFrame
df = pd.concat(all_dfs, ignore_index=True)

# Extract match result
def extract_result(score):
    try:
        score = score.replace("–", "-")
        home, away = map(int, score.split("-"))
        if home > away:
            return "Home Win"
        elif home < away:
            return "Away Win"
        else:
            return "Draw"
    except:
        return None

df["result"] = df["score"].apply(extract_result)
df = df.dropna(subset=["result"])

# Parse goals
df["home_goals"] = df["score"].apply(lambda x: int(x.replace("–", "-").split("-")[0]))
df["away_goals"] = df["score"].apply(lambda x: int(x.replace("–", "-").split("-")[1]))

# Date formatting
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])
df = df.sort_values("date").reset_index(drop=True)

# Add matchday estimate
df["matchday"] = df.groupby("date").ngroup() // 10 + 1

# Team label encoding
le_team = LabelEncoder()
df["home_team_enc"] = le_team.fit_transform(df["home_team"])
df["away_team_enc"] = le_team.transform(df["away_team"])

# Rolling form stats
def generate_team_stats(df, team_col, goals_for_col, goals_against_col, xg_col, role):
    team_stats = []
    team_records = {}

    for _, row in df.iterrows():
        team = row[team_col]
        gf = row[goals_for_col]
        ga = row[goals_against_col]
        xg = row[xg_col]

        last_matches = team_records.get(team, [])
        last_3 = last_matches[-3:]

        points = sum(m["points"] for m in last_3) if last_3 else 0
        gd = sum(m["gf"] - m["ga"] for m in last_3) if last_3 else 0
        avg_xg = sum(m["xg"] for m in last_3) / len(last_3) if last_3 else 0

        team_stats.append({
            f"{role}_recent_points": points,
            f"{role}_recent_gd": gd,
            f"{role}_recent_avg_xg": avg_xg
        })

        outcome = "Draw" if gf == ga else ("Win" if gf > ga else "Loss")
        pt = 1 if outcome == "Draw" else 3 if outcome == "Win" else 0
        last_matches.append({"gf": gf, "ga": ga, "xg": xg, "points": pt})
        team_records[team] = last_matches

    return pd.DataFrame(team_stats)

# Append recent form
home_stats = generate_team_stats(df, "home_team", "home_goals", "away_goals", "home_xg", "home")
away_stats = generate_team_stats(df, "away_team", "away_goals", "home_goals", "away_xg", "away")
df = pd.concat([df, home_stats, away_stats], axis=1)

# Head-to-head results
def calculate_head_to_head(df, home_team_col, away_team_col, result_col):
    h2h_results = {}
    for _, row in df.iterrows():
        home_team = row[home_team_col]
        away_team = row[away_team_col]
        result = row[result_col]

        if (home_team, away_team) not in h2h_results:
            h2h_results[(home_team, away_team)] = {"home_wins": 0, "away_wins": 0, "draws": 0}

        if result == "Home Win":
            h2h_results[(home_team, away_team)]["home_wins"] += 1
        elif result == "Away Win":
            h2h_results[(home_team, away_team)]["away_wins"] += 1
        elif result == "Draw":
            h2h_results[(home_team, away_team)]["draws"] += 1

    return h2h_results

h2h_results = calculate_head_to_head(df, "home_team", "away_team", "result")
df["home_wins_vs_away"] = df.apply(lambda row: h2h_results.get((row["home_team"], row["away_team"]), {"home_wins": 0})["home_wins"], axis=1)
df["away_wins_vs_home"] = df.apply(lambda row: h2h_results.get((row["away_team"], row["home_team"]), {"away_wins": 0})["away_wins"], axis=1)

# Rest days between matches
def calculate_rest_days(df):
    df["home_rest_days"] = df.groupby("home_team")["date"].diff().dt.days
    df["away_rest_days"] = df.groupby("away_team")["date"].diff().dt.days
    return df

df = calculate_rest_days(df)

# Final features
features = [
    "home_xg", "away_xg", "home_team_enc", "away_team_enc", "matchday",
    "home_recent_points", "home_recent_gd", "home_recent_avg_xg",
    "away_recent_points", "away_recent_gd", "away_recent_avg_xg",
    "home_wins_vs_away", "away_wins_vs_home",
    "home_rest_days", "away_rest_days"
]

df = df.dropna(subset=features)
X = df[features]
y = df["result"]

# Train and save model
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

accuracy = accuracy_score(y_test, model.predict(X_test))
print(f"Model trained. Accuracy: {accuracy:.2%}")

joblib.dump(model, "match_predictor_advanced.pkl")
joblib.dump(le_team, "team_label_encoder.pkl")
print("Saved: match_predictor_advanced.pkl and team_label_encoder.pkl")
