import pandas as pd
from pymongo import MongoClient
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import joblib
import os
import pickle
from dotenv import load_dotenv
from pymongo.server_api import ServerApi

# === Load Mongo URI ===
load_dotenv()
uri = os.getenv("URI_MONGO")
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["EPL"]

# === Seasons ===
all_seasons = [
    "2015_2016", "2016_2017", "2017_2018", "2018_2019", "2019_2020",
    "2020_2021", "2021_2022", "2022_2023", "2023_2024", "2024_2025"
]
recent_seasons = ["2021_2022", "2022_2023", "2023_2024", "2024_2025"]

# === Load full data for training ===
all_dfs = []
for season in all_seasons:
    data = list(db[season].find({}, {"_id": 0}))
    if data:
        df = pd.DataFrame(data)
        df["season"] = season
        all_dfs.append(df)

df = pd.concat(all_dfs, ignore_index=True)

# === Preprocess ===
df["score"] = df["score"].str.replace("–", "-")
df[["home_goals", "away_goals"]] = df["score"].str.split("-", expand=True).astype(float)
df = df.dropna(subset=["date", "home_goals", "away_goals"])
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)
df["result"] = df.apply(lambda row: "Home Win" if row["home_goals"] > row["away_goals"]
                        else "Away Win" if row["home_goals"] < row["away_goals"]
                        else "Draw", axis=1)
df["matchday"] = df.groupby("date").ngroup() // 10 + 1

# === Label Encoding ===
le_team = LabelEncoder()
df["home_team_enc"] = le_team.fit_transform(df["home_team"])
df["away_team_enc"] = le_team.transform(df["away_team"])

# === Compute team strengths ===
recent_df = df[df["season"].isin(recent_seasons)]

def compute_strengths(input_df):
    teams_combined = pd.concat([
        input_df[["home_team", "home_goals", "away_goals"]].rename(columns={
            "home_team": "team", "home_goals": "goals_for", "away_goals": "goals_against"
        }),
        input_df[["away_team", "away_goals", "home_goals"]].rename(columns={
            "away_team": "team", "away_goals": "goals_for", "home_goals": "goals_against"
        })
    ])
    grouped = teams_combined.groupby("team").agg(
        matches_played=("goals_for", "count"),
        total_goals_for=("goals_for", "sum"),
        total_goals_against=("goals_against", "sum")
    )
    strengths = {}
    for team, row in grouped.iterrows():
        if row["matches_played"] > 0:
            offense = row["total_goals_for"] / row["matches_played"]
            defense = row["total_goals_against"] / row["matches_played"]
            strengths[team] = {
                "offense_strength": round(offense, 2),
                "defense_weakness": round(defense, 2)
            }
    return strengths

recent_strengths = compute_strengths(recent_df)
all_strengths = compute_strengths(df)

TEAM_STRENGTHS = {}
for team in df["home_team"].unique():
    if team in recent_strengths:
        TEAM_STRENGTHS[team] = recent_strengths[team]
    elif team in all_strengths:
        TEAM_STRENGTHS[team] = all_strengths[team]
    else:
        TEAM_STRENGTHS[team] = {"offense_strength": 1.0, "defense_weakness": 1.0}

# ✅ Save team strengths
with open("epl_team_strengths.pkl", "wb") as f:
    pickle.dump(TEAM_STRENGTHS, f)

# === Add strength columns ===
def get_strength(team, key):
    return TEAM_STRENGTHS.get(team, {}).get(key, 1.0)

df["home_offense_strength"] = df["home_team"].apply(lambda t: get_strength(t, "offense_strength"))
df["home_defense_weakness"] = df["home_team"].apply(lambda t: get_strength(t, "defense_weakness"))
df["away_offense_strength"] = df["away_team"].apply(lambda t: get_strength(t, "offense_strength"))
df["away_defense_weakness"] = df["away_team"].apply(lambda t: get_strength(t, "defense_weakness"))

# === Add XG columns ===
df["home_xg"] = df["home_offense_strength"] * (df["away_defense_weakness"] / 2)
df["away_xg"] = df["away_offense_strength"] * (df["home_defense_weakness"] / 2)

# === Generate recent form (limit to last 3 matches) ===
def generate_recent_form(df):
    records = {}
    for _, row in df.iterrows():
        # Home
        h_team = row["home_team"]
        h_gf = row["home_goals"]
        h_ga = row["away_goals"]
        h_xg = row["home_xg"]
        h_points = 3 if h_gf > h_ga else 1 if h_gf == h_ga else 0
        h_history = records.get(h_team, [])
        h_history.append({"gf": h_gf, "ga": h_ga, "xg": h_xg, "points": h_points})
        records[h_team] = h_history[-3:]

        # Away
        a_team = row["away_team"]
        a_gf = row["away_goals"]
        a_ga = row["home_goals"]
        a_xg = row["away_xg"]
        a_points = 3 if a_gf > a_ga else 1 if a_gf == a_ga else 0
        a_history = records.get(a_team, [])
        a_history.append({"gf": a_gf, "ga": a_ga, "xg": a_xg, "points": a_points})
        records[a_team] = a_history[-3:]
    return records

recent_form = generate_recent_form(df)

# === Add recent form columns to df ===
def get_recent_stats(team):
    history = recent_form.get(team, [])
    points = sum(m["points"] for m in history)
    gd = sum(m["gf"] - m["ga"] for m in history)
    avg_xg = sum(m["xg"] for m in history) / len(history) if history else 0
    return points, gd, avg_xg

df["home_recent_points"], df["home_recent_gd"], df["home_recent_avg_xg"] = zip(*df["home_team"].apply(get_recent_stats))
df["away_recent_points"], df["away_recent_gd"], df["away_recent_avg_xg"] = zip(*df["away_team"].apply(get_recent_stats))

# === Head-to-head features ===
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

# === Final features list ===
features = [
    "home_xg", "away_xg",
    "home_team_enc", "away_team_enc", "matchday",
    "home_recent_points", "home_recent_gd", "home_recent_avg_xg",
    "away_recent_points", "away_recent_gd", "away_recent_avg_xg",
    "home_wins_vs_away", "away_wins_vs_home",
    "home_offense_strength", "home_defense_weakness",
    "away_offense_strength", "away_defense_weakness"
]

# === Train model ===
df = df.dropna(subset=features)
X = df[features]
y = df["result"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

acc = accuracy_score(y_test, model.predict(X_test))
print(f"\nEPL Model Trained. Accuracy: {acc:.2%}")

# === Save model and encoder ===
joblib.dump(model, "epl_match_predictor_advanced.pkl")
joblib.dump(le_team, "epl_team_label_encoder.pkl")
with open("epl_recent_form.pkl", "wb") as f:
    pickle.dump(recent_form, f)
with open("epl_h2h_results.pkl", "wb") as f:
    pickle.dump(h2h_results, f)

print("Saved: epl_match_predictor_advanced.pkl, epl_team_label_encoder.pkl, recent_form, h2h")
