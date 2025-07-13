import pandas as pd
from pymongo import MongoClient
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import joblib
from dotenv import load_dotenv
import os
import unicodedata
import pickle

# === Load env ===
load_dotenv()
uri = os.getenv("URI_MONGO")
client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)
db = client["LaLiga"]

# === Seasons ===
all_seasons = [
    "2017_18", "2018_19", "2019_20", "2020_21",
    "2021_22", "2022_23", "2023_24", "2024_25"
]
recent_seasons = ["2021_22", "2022_23", "2023_24"]

# === Load and merge data ===
all_dfs = []
for season in all_seasons:
    data = list(db[season].find({}, {"_id": 0}))
    if data:
        df = pd.DataFrame(data)
        df["season"] = season
        all_dfs.append(df)
df = pd.concat(all_dfs, ignore_index=True)

# === Normalize scores ===
def extract_result(score):
    try:
        score = score.replace("–", "-")
        home, away = map(int, score.split("-"))
        if home > away:
            return "Home Win"
        elif home < away:
            return "Away Win"
        return "Draw"
    except:
        return None

df["result"] = df["score"].apply(extract_result)
df = df.dropna(subset=["result"])
df["home_goals"] = df["score"].apply(lambda x: int(x.replace("–", "-").split("-")[0]))
df["away_goals"] = df["score"].apply(lambda x: int(x.replace("–", "-").split("-")[1]))
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
df["matchday"] = df.groupby("date").ngroup() // 10 + 1

# === Normalize team names ===
TEAM_NAME_MAP = {
    "Deportivo Alaves": "Alaves", "Almeria": "Almeria", "Athletic Club": "Athletic Club",
    "Club Atletico de Madrid": "Atletico Madrid", "FC Barcelona": "Barcelona", "Real Betis Balompie": "Betis",
    "RC Celta de Vigo": "Celta Vigo", "Cadiz CF": "Cadiz", "Eibar": "Eibar", "Elche CF": "Elche",
    "RCD Espanyol de Barcelona": "Espanyol", "Getafe CF": "Getafe", "Girona FC": "Girona", "Granada CF": "Granada",
    "Huesca": "Huesca", "Deportivo La Coruna": "La Coruna", "UD Las Palmas": "Las Palmas", "CD Leganes": "Leganes",
    "Levante UD": "Levante", "RCD Mallorca": "Mallorca", "Malaga CF": "Malaga", "CA Osasuna": "Osasuna",
    "Rayo Vallecano de Madrid": "Rayo Vallecano", "Real Madrid CF": "Real Madrid",
    "Real Sociedad de Futbol": "Real Sociedad", "Sevilla FC": "Sevilla", "Valencia CF": "Valencia",
    "Real Valladolid CF": "Valladolid", "Villarreal CF": "Villarreal"
}
def normalize(name):
    name = TEAM_NAME_MAP.get(name, name)
    return unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8").strip()

df["home_team"] = df["home_team"].apply(normalize)
df["away_team"] = df["away_team"].apply(normalize)

# === Encode team names ===
le_team = LabelEncoder()
df["home_team_enc"] = le_team.fit_transform(df["home_team"])
df["away_team_enc"] = le_team.transform(df["away_team"])

# === Compute team strengths ===
def compute_strengths(df_subset):
    combined = pd.concat([
        df_subset[["home_team", "home_goals", "away_goals"]].rename(columns={"home_team": "team", "home_goals": "goals_for", "away_goals": "goals_against"}),
        df_subset[["away_team", "away_goals", "home_goals"]].rename(columns={"away_team": "team", "away_goals": "goals_for", "home_goals": "goals_against"})
    ])
    grouped = combined.groupby("team").agg(matches_played=("goals_for", "count"),
                                           total_goals_for=("goals_for", "sum"),
                                           total_goals_against=("goals_against", "sum"))
    return {
        team: {
            "offense_strength": round(row["total_goals_for"] / row["matches_played"], 2),
            "defense_weakness": round(row["total_goals_against"] / row["matches_played"], 2)
        }
        for team, row in grouped.iterrows()
    }

recent_strengths = compute_strengths(df[df["season"].isin(recent_seasons)])
all_strengths = compute_strengths(df)

TEAM_STRENGTHS = {}
for team in df["home_team"].unique():
    if team in recent_strengths:
        TEAM_STRENGTHS[team] = recent_strengths[team]
    elif team in all_strengths:
        TEAM_STRENGTHS[team] = all_strengths[team]
    else:
        TEAM_STRENGTHS[team] = {"offense_strength": 1.0, "defense_weakness": 1.0}

with open("laliga_team_strengths.pkl", "wb") as f:
    pickle.dump(TEAM_STRENGTHS, f)

# === Add strength features ===
def get_strength(team, key):
    return TEAM_STRENGTHS.get(team, {}).get(key, 1.0)

df["home_offense_strength"] = df["home_team"].apply(lambda t: get_strength(t, "offense_strength"))
df["home_defense_weakness"] = df["home_team"].apply(lambda t: get_strength(t, "defense_weakness"))
df["away_offense_strength"] = df["away_team"].apply(lambda t: get_strength(t, "offense_strength"))
df["away_defense_weakness"] = df["away_team"].apply(lambda t: get_strength(t, "defense_weakness"))

df["home_xg"] = df["home_offense_strength"] * (df["away_defense_weakness"] / 2)
df["away_xg"] = df["away_offense_strength"] * (df["home_defense_weakness"] / 2)

# === Generate and limit recent form to last 3 matches per team ===
def generate_recent_form(df):
    records = {}
    for _, row in df.iterrows():
        # Home team
        h_team = row["home_team"]
        h_gf = row["home_goals"]
        h_ga = row["away_goals"]
        h_xg = row.get("home_xg", 0)
        h_points = 3 if h_gf > h_ga else 1 if h_gf == h_ga else 0
        h_history = records.get(h_team, [])
        h_history.append({"gf": h_gf, "ga": h_ga, "xg": h_xg, "points": h_points})
        records[h_team] = h_history[-3:]

        # Away team
        a_team = row["away_team"]
        a_gf = row["away_goals"]
        a_ga = row["home_goals"]
        a_xg = row.get("away_xg", 0)
        a_points = 3 if a_gf > a_ga else 1 if a_gf == a_ga else 0
        a_history = records.get(a_team, [])
        a_history.append({"gf": a_gf, "ga": a_ga, "xg": a_xg, "points": a_points})
        records[a_team] = a_history[-3:]
    return records

recent_form = generate_recent_form(df)

# === Add recent form features to df ===
def get_recent_stats(team):
    history = recent_form.get(team, [])
    points = sum(m["points"] for m in history)
    gd = sum(m["gf"] - m["ga"] for m in history)
    avg_xg = sum(m["xg"] for m in history) / len(history) if history else 0
    return points, gd, avg_xg

df["home_recent_points"], df["home_recent_gd"], df["home_recent_avg_xg"] = zip(*df["home_team"].apply(get_recent_stats))
df["away_recent_points"], df["away_recent_gd"], df["away_recent_avg_xg"] = zip(*df["away_team"].apply(get_recent_stats))

with open("laliga_recent_form.pkl", "wb") as f:
    pickle.dump(recent_form, f)

# === Head-to-head ===
def calculate_head_to_head(df, home_col, away_col, result_col):
    results = {}
    for _, row in df.iterrows():
        home, away, result = row[home_col], row[away_col], row[result_col]
        if (home, away) not in results:
            results[(home, away)] = {"home_wins": 0, "away_wins": 0, "draws": 0}
        if result == "Home Win":
            results[(home, away)]["home_wins"] += 1
        elif result == "Away Win":
            results[(home, away)]["away_wins"] += 1
        elif result == "Draw":
            results[(home, away)]["draws"] += 1
    return results

h2h_results = calculate_head_to_head(df, "home_team", "away_team", "result")
df["home_wins_vs_away"] = df.apply(lambda r: h2h_results.get((r["home_team"], r["away_team"]), {}).get("home_wins", 0), axis=1)
df["away_wins_vs_home"] = df.apply(lambda r: h2h_results.get((r["away_team"], r["home_team"]), {}).get("away_wins", 0), axis=1)

with open("laliga_h2h_results.pkl", "wb") as f:
    pickle.dump(h2h_results, f)

# === Features for model ===
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
print(f"\\La Liga Model Trained. Accuracy: {acc:.2%}")

# === Save ===
joblib.dump(model, "laliga_match_predictor_advanced.pkl")
joblib.dump(le_team, "laliga_team_label_encoder.pkl")

print("Saved: model, encoder, strengths, recent_form, h2h")
