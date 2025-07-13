import os
import pickle
from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import requests
import joblib
from datetime import datetime
import numpy as np
import unicodedata

# === Load Environment ===
load_dotenv()
API_TOKEN = os.getenv('FOOTBALL_API_KEY')
API_URL = 'https://api.football-data.org/v4'
CACHE = {}

# === Flask App Init ===
app = Flask(__name__, static_folder='frontend_back/dist', static_url_path='')
CORS(app)

laliga_model = joblib.load(r"laliga_match_predictor_advanced.pkl")
print("La Liga model class order:", laliga_model.classes_)

prem_model = joblib.load(r"epl_match_predictor_advanced.pkl")
print("Premier League model class order:", prem_model.classes_)


MODELS = {
    "laliga": {
        "model": joblib.load("laliga_match_predictor_advanced.pkl"),
        "encoder": joblib.load("laliga_team_label_encoder.pkl"),
        "strengths": pickle.load(open("laliga_team_strengths.pkl", "rb")),
        "recent_form": pickle.load(open("laliga_recent_form.pkl", "rb")),
        "h2h_results": pickle.load(open("laliga_h2h_results.pkl", "rb"))
    },
    "prem": {
        "model": joblib.load("epl_match_predictor_advanced.pkl"),
        "encoder": joblib.load("epl_team_label_encoder.pkl"),
        "strengths": pickle.load(open("epl_team_strengths.pkl", "rb")),
        "recent_form": pickle.load(open("epl_recent_form.pkl", "rb")),
        "h2h_results": pickle.load(open("epl_h2h_results.pkl", "rb"))
    }
}

TEAM_NAME_MAP = {
    # Premier League - map API names to model keys
    "Arsenal FC": "Arsenal",
    "Aston Villa FC": "Aston Villa",
    "AFC Bournemouth": "Bournemouth",
    "Brentford FC": "Brentford",
    "Brighton & Hove Albion FC": "Brighton",
    "Burnley FC": "Burnley",
    "Cardiff City FC": "Cardiff",
    "Chelsea FC": "Chelsea",
    "Crystal Palace FC": "Crystal Palace",
    "Everton FC": "Everton",
    "Fulham FC": "Fulham",
    "Huddersfield Town AFC": "Huddersfield",
    "Hull City AFC": "Hull",
    "Ipswich Town FC": "Ipswich",
    "Leeds United FC": "Leeds",
    "Leicester City FC": "Leicester",
    "Liverpool FC": "Liverpool",
    "Luton Town FC": "Luton",
    "Manchester City FC": "Manchester City",
    "Manchester United FC": "Manchester United",
    "Middlesbrough FC": "Middlesbrough",
    "Newcastle United FC": "Newcastle United",
    "Norwich City FC": "Norwich",
    "Nottingham Forest FC": "Nottingham Forest",
    "Sheffield United FC": "Sheffield United",
    "Southampton FC": "Southampton",
    "Stoke City FC": "Stoke",
    "Sunderland AFC": "Sunderland",
    "Swansea City AFC": "Swansea",
    "Tottenham Hotspur FC": "Tottenham",
    "Watford FC": "Watford",
    "West Bromwich Albion FC": "West Bromwich Albion",
    "West Ham United FC": "West Ham",
    "Wolverhampton Wanderers FC": "Wolverhampton Wanderers",

    # La Liga
    "FC Barcelona": "Barcelona",
    "Real Madrid CF": "Real Madrid",
    "Club Atlético de Madrid": "Atletico Madrid",
    "Athletic Club": "Athletic Club",
    "Villarreal CF": "Villarreal",
    "Real Betis Balompié": "Betis",
    "RC Celta de Vigo": "Celta Vigo",
    "Rayo Vallecano de Madrid": "Rayo Vallecano",
    "CA Osasuna": "Osasuna",
    "RCD Mallorca": "Mallorca",
    "Real Sociedad de Fútbol": "Real Sociedad",
    "Valencia CF": "Valencia",
    "Getafe CF": "Getafe",
    "RCD Espanyol de Barcelona": "Espanyol",
    "Deportivo Alavés": "Alaves",
    "Girona FC": "Girona",
    "Sevilla FC": "Sevilla",
    "Levante UD": "Levante",
    "Elche CF": "Elche",
    "Real Oviedo": "Real Oviedo"
}

STATIC_TEAMS = [
    {"id": 57, "name": "Arsenal"},
    {"id": 58, "name": "Aston Villa"},
    {"id": 1044, "name": "AFC Bournemouth"},
    {"id": 402, "name": "Brentford FC"},
    {"id": 397, "name": "Brighton & Hove Albion FC"},
    {"id": 328, "name": "Burnley FC"},
    {"id": 68, "name": "Chelsea"},
    {"id": 354, "name": "Crystal Palace"},
    {"id": 62, "name": "Everton"},
    {"id": 63, "name": "Fulham FC"},
    {"id": 341, "name": "Leeds United FC"},
    {"id": 64, "name": "Liverpool"},
    {"id": 65, "name": "Manchester City"},
    {"id": 66, "name": "Manchester United"},
    {"id": 67, "name": "Newcastle United"},
    {"id": 351, "name": "Nottingham Forest FC"},
    {"id": 71, "name": "Sunderland AFC"},
    {"id": 73, "name": "Tottenham Hotspur"},
    {"id": 563, "name": "West Ham United FC"},
    {"id": 76, "name": "Wolverhampton Wanderers"},

    # La Liga Teams
    {"id": 81, "name": "Barcelona"},
    {"id": 86, "name": "Real Madrid"},
    {"id": 78, "name": "Atletico Madrid"},
    {"id": 77, "name": "Athletic Club"},
    {"id": 94, "name": "Villarreal"},
    {"id": 90, "name": "Betis"},
    {"id": 558, "name": "Celta Vigo"},
    {"id": 87, "name": "Rayo Vallecano"},
    {"id": 79, "name": "Osasuna"},
    {"id": 89, "name": "Mallorca"},
    {"id": 92, "name": "Real Sociedad"},
    {"id": 95, "name": "Valencia"},
    {"id": 82, "name": "Getafe"},
    {"id": 80, "name": "Espanyol"},
    {"id": 263, "name": "Alaves"},
    {"id": 298, "name": "Girona"},
    {"id": 559, "name": "Sevilla"},
    {"id": 88, "name": "Levante"},
    {"id": 285, "name": "Elche"},
    {"id": 1048, "name": "Real Oviedo"}
]

def normalize_team_name(name):
    mapped = TEAM_NAME_MAP.get(name, name)
    return unicodedata.normalize("NFKD", mapped).encode("ASCII", "ignore").decode("utf-8").strip()

def predict_match_with_model(home_team, away_team, return_features=True, verbose=False, matchday=None, league_hint="laliga"):
    import numpy as np
    import pandas as pd

    home = normalize_team_name(home_team)
    away = normalize_team_name(away_team)

    # Determine league
    league = None
    if home in MODELS["laliga"]["strengths"] and away in MODELS["laliga"]["strengths"]:
        league = "laliga"
    elif home in MODELS["prem"]["strengths"] and away in MODELS["prem"]["strengths"]:
        league = "prem"
    else:
        return "Unknown", [0.0, 0.0, 0.0], 0.0, 0.0, []

    encoder = MODELS[league]["encoder"]
    model = MODELS[league]["model"]
    strengths = MODELS[league]["strengths"]
    recent_form = MODELS[league]["recent_form"]
    h2h_results = MODELS[league]["h2h_results"]

    try:
        home_enc = encoder.transform([home])[0]
        away_enc = encoder.transform([away])[0]
    except:
        return "Unknown", [0.0, 0.0, 0.0], 0.0, 0.0, []

    h = strengths[home]
    a = strengths[away]

    # Matchday logic with cache fallback
    if matchday is None:
        cache_key = f"matchday_{league}"
        if cache_key in CACHE and is_cache_valid(CACHE[cache_key]['time']):
            matchday = CACHE[cache_key]['data'].get("matchday", 0)
        else:
            matchday = 0  # fallback if nothing available
            print(f"[WARN] matchday not provided and not cached for {home} vs {away}. Using default boost.")

    # Apply safe fallback strength boost
    if matchday > 0:
        strength_boost = max(1.0, 2.0 - 0.3 * (matchday - 1))
    else:
        strength_boost = 1.0

    if verbose:
        print(f"Team strength boost applied: {strength_boost:.2f}")

    home_xg = (h["offense_strength"] * strength_boost) * ((a["defense_weakness"] * strength_boost) / 2)
    away_xg = (a["offense_strength"] * strength_boost) * ((h["defense_weakness"] * strength_boost) / 2)

    home_avg_xg = round(home_xg, 2)
    away_avg_xg = round(away_xg, 2)

    # Recent form
    def get_recent_stats(team, fallback_xg):
        recent_matches = recent_form.get(team, [])
        last_n = max(0, min(matchday - 1, 3))
        last_matches = recent_matches[-last_n:]
        pts = sum(m["points"] for m in last_matches) if last_matches else 0.0
        gd = sum(m["gf"] - m["ga"] for m in last_matches) if last_matches else 0.0
        avg_xg = sum(m["gf"] for m in last_matches) / len(last_matches) if last_matches else fallback_xg
        return pts, gd, avg_xg

    home_points, home_gd, home_avg_xg_actual = get_recent_stats(home, home_avg_xg)
    away_points, away_gd, away_avg_xg_actual = get_recent_stats(away, away_avg_xg)

    # Head-to-head
    h2h = h2h_results.get((home, away), {})
    rev_h2h = h2h_results.get((away, home), {})
    home_wins_vs_away = h2h.get("home_wins", 0)
    away_wins_vs_home = rev_h2h.get("away_wins", 0)

    # Final feature vector
    features = [
        home_xg, away_xg,
        home_enc, away_enc, matchday,
        home_points, home_gd, home_avg_xg_actual,
        away_points, away_gd, away_avg_xg_actual,
        home_wins_vs_away, away_wins_vs_home,
        h["offense_strength"], h["defense_weakness"],
        a["offense_strength"], a["defense_weakness"]
    ]

    feature_names = [
        "home_xg", "away_xg",
        "home_team_enc", "away_team_enc", "matchday",
        "home_recent_points", "home_recent_gd", "home_recent_avg_xg",
        "away_recent_points", "away_recent_gd", "away_recent_avg_xg",
        "home_wins_vs_away", "away_wins_vs_home",
        "home_offense_strength", "home_defense_weakness",
        "away_offense_strength", "away_defense_weakness"
    ]

    features_df = pd.DataFrame([features], columns=feature_names)
    raw_probs = model.predict_proba(features_df)[0]
    predicted_result = model.classes_[np.argmax(raw_probs)]

    if return_features:
        return predicted_result, raw_probs.tolist(), home_avg_xg, away_avg_xg, features
    else:
        return predicted_result, raw_probs.tolist(), home_avg_xg, away_avg_xg




def format_date_nice(utc):
    dt = datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ")
    day = dt.day
    suffix = 'th' if 11 <= day <= 13 else {1:'st',2:'nd',3:'rd'}.get(day % 10, 'th')
    return f"{day}{suffix} {dt.strftime('%B')}"

def get_latest_matchday_fixtures(league='laliga'):
    competition_id = {
        'laliga': '2014',
        'epl': '2021',
        'prem': '2021'
    }.get(league)

    if not competition_id:
        print("Invalid league:", league)
        return [], None

    headers = {'X-Auth-Token': API_TOKEN}

    comp_url = f"https://api.football-data.org/v4/competitions/{competition_id}"
    comp_resp = requests.get(comp_url, headers=headers)
    if comp_resp.status_code != 200:
        print("Failed to fetch competition info:", comp_resp.status_code, comp_resp.text)
        return [], None

    current_md = comp_resp.json().get("currentSeason", {}).get("currentMatchday")
    if not current_md:
        print("No current matchday found for league:", league)
        return [], None

    print(f"League: {league} | Matchday: {current_md}")

    matches_url = f"https://api.football-data.org/v4/competitions/{competition_id}/matches?matchday={current_md}"
    matches_resp = requests.get(matches_url, headers=headers)
    if matches_resp.status_code != 200:
        print("Failed to fetch matches:", matches_resp.status_code, matches_resp.text)
        return [], current_md

    matches = matches_resp.json().get("matches", [])
    result_list = []

    for m in matches:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]

        # 5-value return unpacking
        pred, conf, home_xg, away_xg, _ = predict_match_with_model(
            home, away, matchday=current_md, return_features=True
        )

        if pred == "Unknown":
            print(f"Skipping unknown prediction: {home} vs {away}")
            continue

        ft = m.get("score", {}).get("fullTime", {})
        home_goals = ft.get("home") if ft.get("home") is not None else "-"
        away_goals = ft.get("away") if ft.get("away") is not None else "-"

        result_list.append({
            "utcDate": m["utcDate"],
            "homeTeam": {"name": home},
            "awayTeam": {"name": away},
            "score": {"fullTime": {"home": home_goals, "away": away_goals}},
            "prediction": {
                "result": pred,
                "confidence": conf,
                "expected_goals": {
                    "home": home_xg,
                    "away": away_xg
                }
            },
            "formatted_date": format_date_nice(m["utcDate"])
        })

    print(f"Fixtures returned: {len(result_list)}")
    return result_list, current_md



def is_cache_valid(ts, seconds=300):
    return (datetime.now() - ts).total_seconds() < seconds

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/epl/teams')
def api_epl_teams():
    return jsonify([t for t in STATIC_TEAMS if t['name'] in MODELS["prem"]["strengths"]])

@app.route('/api/laliga/teams')
def api_laliga_teams():
    return jsonify([t for t in STATIC_TEAMS if t['name'] in MODELS["laliga"]["strengths"]])

@app.route('/api/fixtures/next/<int:team_id>')
def api_next(team_id):
    league = request.args.get("league", "laliga")
    key = f"{team_id}_next_{league}"
    if key in CACHE and is_cache_valid(CACHE[key]['time']):
        print(f"[CACHE HIT] /api/fixtures/next/{team_id}?league={league}")
        return jsonify(CACHE[key]['data'])

    print(f"[API CALL] /api/fixtures/next/{team_id}?league={league}")

    _, latest_matchday = get_latest_matchday_fixtures(league=league)
    if latest_matchday is None:
        return jsonify([])

    headers = {'X-Auth-Token': API_TOKEN}
    res = requests.get(f"{API_URL}/teams/{team_id}/matches?status=SCHEDULED&limit=5", headers=headers)
    fixtures = []

    if res.status_code == 200:
        for m in res.json().get("matches", []):
            pred, proba, home_xg, away_xg, _ = predict_match_with_model(
                m["homeTeam"]["name"], m["awayTeam"]["name"], matchday=latest_matchday
            )
            model = MODELS["laliga" if league == "laliga" else "prem"]["model"]
            confidence = dict(zip(model.classes_, proba))
            fixtures.append({
                "utcDate": m["utcDate"],
                "home": m["homeTeam"]["name"],
                "away": m["awayTeam"]["name"],
                "prediction": {
                    "result": pred,
                    "confidence": confidence,
                    "expected_goals": {
                        "home": home_xg,
                        "away": away_xg
                    }
                }
            })
        CACHE[key] = {"data": fixtures, "time": datetime.now()}
    return jsonify(fixtures)


@app.route('/api/fixtures/last/<int:team_id>')
def api_last(team_id):
    league = request.args.get("league", "laliga")
    key = f"{team_id}_last_{league}"
    if key in CACHE and is_cache_valid(CACHE[key]['time']):
        print(f"[CACHE HIT] /api/fixtures/last/{team_id}?league={league}")
        return jsonify(CACHE[key]['data'])

    print(f"[API CALL] /api/fixtures/last/{team_id}?league={league}")

    _, latest_matchday = get_latest_matchday_fixtures(league=league)
    if latest_matchday is None:
        return jsonify([])

    headers = {'X-Auth-Token': API_TOKEN}
    res = requests.get(f"{API_URL}/teams/{team_id}/matches?status=FINISHED&limit=5", headers=headers)
    results = []

    if res.status_code == 200:
        for m in res.json().get("matches", []):
            pred, proba, home_xg, away_xg, _ = predict_match_with_model(
                m["homeTeam"]["name"], m["awayTeam"]["name"], matchday=latest_matchday
            )
            model = MODELS["laliga" if league == "laliga" else "prem"]["model"]
            confidence = dict(zip(model.classes_, proba))
            ft = m["score"]["fullTime"]
            results.append({
                "utcDate": m["utcDate"],
                "home": m["homeTeam"]["name"],
                "away": m["awayTeam"]["name"],
                "score": ft,
                "prediction": {
                    "result": pred,
                    "confidence": confidence,
                    "expected_goals": {
                        "home": home_xg,
                        "away": away_xg
                    }
                }
            })
        CACHE[key] = {"data": results, "time": datetime.now()}
    return jsonify(results)


@app.route('/api/fixtures/matchday', methods=['GET'])
def api_matchday():
    league = request.args.get('league', 'laliga')
    key = f"matchday_{league}"

    if key in CACHE and is_cache_valid(CACHE[key]['time']):
        print(f"[CACHE HIT] /api/fixtures/matchday?league={league}")
        return jsonify(CACHE[key]['data'])

    print(f"[API CALL] /api/fixtures/matchday?league={league}")

    # This function already returns fixtures with predictions and formatted data
    fixtures, matchday_num = get_latest_matchday_fixtures(league=league)

    payload = {
        "matchday": matchday_num,
        "fixtures": fixtures
    }

    CACHE[key] = {
        "data": payload,
        "time": datetime.now()
    }

    return jsonify(payload)


if __name__ == '__main__':
    if os.getenv("DEBUG_PREDICTION") == "1":
        home_team = "RCD Espanyol de Barcelona"
        away_team = "Club Atlético de Madrid"
        result, confidence, home_xg, away_xg, features = predict_match_with_model(
            home_team, away_team, return_features=True, verbose=False
        )
        print("Prediction Example ---")
        print(f"{home_team} vs {away_team}")
        print("Predicted Result:", result)
        print("Confidence Scores [Home Win, Draw, Away Win]:", confidence)
        print("Expected Goals (Home, Away):", home_xg, away_xg)

        # Unpack features
        (
            f_home_xg, f_away_xg,
            f_home_enc, f_away_enc, f_matchday,
            f_home_points, f_home_gd, f_home_avg_xg,
            f_away_points, f_away_gd, f_away_avg_xg,
            f_home_wins_vs_away, f_away_wins_vs_home,
            f_home_off_str, f_home_def_weak,
            f_away_off_str, f_away_def_weak
        ) = features

        print("\nDetailed Feature Breakdown:")
        print(f"Matchday: {f_matchday}")
        print(f"Home Team Encoded: {f_home_enc}")
        print(f"Away Team Encoded: {f_away_enc}")
        print(f"Home Expected xG (calculated): {f_home_xg}")
        print(f"Away Expected xG (calculated): {f_away_xg}")
        print(f"Home Recent Points (last 3 matches): {f_home_points}")
        print(f"Away Recent Points (last 3 matches): {f_away_points}")
        print(f"Home Goal Difference (last 3 matches): {f_home_gd}")
        print(f"Away Goal Difference (last 3 matches): {f_away_gd}")
        print(f"Home Avg Actual xG (last 3 matches): {f_home_avg_xg}")
        print(f"Away Avg Actual xG (last 3 matches): {f_away_avg_xg}")
        print(f"Home Wins vs Away (H2H): {f_home_wins_vs_away}")
        print(f"Away Wins vs Home (H2H): {f_away_wins_vs_home}")
        print(f"Home Offense Strength: {f_home_off_str}")
        print(f"Home Defense Weakness: {f_home_def_weak}")
        print(f"Away Offense Strength: {f_away_off_str}")
        print(f"Away Defense Weakness: {f_away_def_weak}")

    # Start Flask server
    app.run(debug=True)

