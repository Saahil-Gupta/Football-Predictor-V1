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
import pickle  # for saving team strengths

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

# Matchday estimation
df["matchday"] = df.groupby("date").ngroup() // 10 + 1

# Normalize team names
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

# Encode team names
le_team = LabelEncoder()
df["home_team_enc"] = le_team.fit_transform(df["home_team"])
df["away_team_enc"] = le_team.transform(df["away_team"])

# Compute team strengths
teams_combined = pd.concat([
    df[["home_team", "home_goals", "away_goals"]].rename(columns={"home_team": "team", "home_goals": "goals_for", "away_goals": "goals_against"}),
    df[["away_team", "away_goals", "home_goals"]].rename(columns={"away_team": "team", "away_goals": "goals_for", "home_goals": "goals_against"})
])

grouped = teams_combined.groupby("team").agg(
    matches_played=("goals_for", "count"),
    total_goals_for=("goals_for", "sum"),
    total_goals_against=("goals_against", "sum")
)

TEAM_STRENGTHS = {}
for team, row in grouped.iterrows():
    offense = row["total_goals_for"] / row["matches_played"]
    defense = row["total_goals_against"] / row["matches_played"]
    TEAM_STRENGTHS[team] = {
        "offense_strength": round(offense, 2),
        "defense_weakness": round(defense, 2)
    }

with open("team_strengths.pkl", "wb") as f:
    pickle.dump(TEAM_STRENGTHS, f)

def get_strength(team, key):
    return TEAM_STRENGTHS.get(team, {}).get(key, 0.5)

df["home_offense_strength"] = df["home_team"].apply(lambda t: get_strength(t, "offense_strength"))
df["home_defense_weakness"] = df["home_team"].apply(lambda t: get_strength(t, "defense_weakness"))
df["away_offense_strength"] = df["away_team"].apply(lambda t: get_strength(t, "offense_strength"))
df["away_defense_weakness"] = df["away_team"].apply(lambda t: get_strength(t, "defense_weakness"))

# Form stats
def generate_team_stats(df, team_col, goals_for_col, goals_against_col, xg_col, role):
    team_stats = []
    team_records = {}

    for _, row in df.iterrows():
        team = row[team_col]
        gf = row[goals_for_col]
        ga = row[goals_against_col]
        xg = row.get(xg_col, 0)

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

        pt = 1 if gf == ga else 3 if gf > ga else 0
        last_matches.append({"gf": gf, "ga": ga, "xg": xg, "points": pt})
        team_records[team] = last_matches

    return pd.DataFrame(team_stats)

df = pd.concat([
    df,
    generate_team_stats(df, "home_team", "home_goals", "away_goals", "home_xg", "home"),
    generate_team_stats(df, "away_team", "away_goals", "home_goals", "away_xg", "away")
], axis=1)

# Head-to-head stats
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

# Rest days
df["home_rest_days"] = df.groupby("home_team")["date"].diff().dt.days
df["away_rest_days"] = df.groupby("away_team")["date"].diff().dt.days

# Final features
features = [
    "home_xg", "away_xg", "home_team_enc", "away_team_enc", "matchday",
    "home_recent_points", "home_recent_gd", "home_recent_avg_xg",
    "away_recent_points", "away_recent_gd", "away_recent_avg_xg",
    "home_wins_vs_away", "away_wins_vs_home",
    "home_rest_days", "away_rest_days",
    "home_offense_strength", "home_defense_weakness",
    "away_offense_strength", "away_defense_weakness"
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
print("Saved: match_predictor_advanced.pkl, team_label_encoder.pkl, and team_strengths.pkl")
