import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
import requests
import joblib
from datetime import datetime
import numpy as np
import unicodedata
import random

# === Team Mapping & Static Team List ===
# Map API names to model/DB names
TEAM_NAME_MAP = {
    "Deportivo Alavés": "Alaves",
    "Almeria": "Almeria",
    "Athletic Club": "Athletic Club",
    "Club Atlético de Madrid": "Atletico Madrid",
    "FC Barcelona": "Barcelona",
    "Real Betis Balompié": "Betis",
    "RC Celta de Vigo": "Celta Vigo",
    "Cadiz CF": "Cadiz",
    "Eibar": "Eibar",
    "Elche CF": "Elche",
    "RCD Espanyol de Barcelona": "Espanyol",
    "Getafe CF": "Getafe",
    "Girona FC": "Girona",
    "Granada CF": "Granada",
    "Huesca": "Huesca",
    "Deportivo La Coruna": "La Coruna",
    "UD Las Palmas": "Las Palmas",
    "CD Leganés": "Leganes",
    "Levante UD": "Levante",
    "RCD Mallorca": "Mallorca",
    "Malaga CF": "Malaga",
    "CA Osasuna": "Osasuna",
    "Rayo Vallecano de Madrid": "Rayo Vallecano",
    "Real Madrid CF": "Real Madrid",
    "Real Sociedad de Fútbol": "Real Sociedad",
    "Sevilla FC": "Sevilla",
    "Valencia CF": "Valencia",
    "Real Valladolid CF": "Valladolid",
    "Villarreal CF": "Villarreal"
}

# Static list of La Liga teams with their API IDs and display names
STATIC_TEAMS = [
    {"id": 81,  "name": "Barcelona"},
    {"id": 86,  "name": "Real Madrid"},
    {"id": 78,  "name": "Atletico Madrid"},
    {"id": 77,  "name": "Athletic Club"},
    {"id": 94,  "name": "Villarreal"},
    {"id": 90,  "name": "Betis"},
    {"id": 558, "name": "Celta Vigo"},
    {"id": 87,  "name": "Rayo Vallecano"},
    {"id": 79,  "name": "Osasuna"},
    {"id": 89,  "name": "Mallorca"},
    {"id": 92,  "name": "Real Sociedad"},
    {"id": 95,  "name": "Valencia"},
    {"id": 82,  "name": "Getafe"},
    {"id": 80,  "name": "Espanyol"},
    {"id": 263, "name": "Alaves"},
    {"id": 298, "name": "Girona"},
    {"id": 559, "name": "Sevilla"},
    {"id": 745, "name": "Leganes"},
    {"id": 275, "name": "Las Palmas"},
    {"id": 250, "name": "Valladolid"}
]

# === Load Environment & Initialize ===
load_dotenv()
app = Flask(__name__)
CORS(app)

API_TOKEN = os.getenv('FOOTBALL_API_KEY')
API_URL = 'https://api.football-data.org/v4'
CACHE = {}

# === Load ML models & strengths ===
model = joblib.load("match_predictor_advanced.pkl")
le_team = joblib.load("team_label_encoder.pkl")
TEAM_STRENGTHS = joblib.load("team_strengths.pkl")

# === Helper Functions ===
def normalize_team_name(name):
    mapped = TEAM_NAME_MAP.get(name, name)
    return unicodedata.normalize("NFKD", mapped).encode("ASCII", "ignore").decode("utf-8").strip()


def predict_match(home_team, away_team):
    home = normalize_team_name(home_team)
    away = normalize_team_name(away_team)
    if home not in TEAM_STRENGTHS or away not in TEAM_STRENGTHS:
        return None, None
    h = TEAM_STRENGTHS[home]
    a = TEAM_STRENGTHS[away]
    score = (h['offense_strength'] - a['defense_weakness']) - (a['offense_strength'] - h['defense_weakness'])
    noise = random.uniform(-0.1, 0.1)
    total = score + noise
    if total > 0.15:
        return 'Home Win', [0.75, 0.15, 0.1]
    elif total < -0.15:
        return 'Away Win', [0.1, 0.15, 0.75]
    else:
        return 'Draw', [0.25, 0.5, 0.25]


def is_cache_valid(ts, seconds=60):
    return (datetime.now() - ts).total_seconds() < seconds


def format_date_nice(utc):
    dt = datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ")
    day = dt.day
    suffix = 'th' if 11 <= day <= 13 else {1:'st',2:'nd',3:'rd'}.get(day % 10, 'th')
    return f"{day}{suffix} {dt.strftime('%B')}"


def get_latest_matchday_fixtures():
    """
        Queries the Football‐Data API to find the highest (latest) matchday in La Liga,
        then returns a tuple: (list_of_fixture_dicts, latest_matchday_number).
        Each fixture dict includes:
        - 'utcDate'
        - 'homeTeam': { 'name': … }
        - 'awayTeam': { 'name': … }
        - 'score': { 'fullTime': { 'home': X, 'away': Y } }
        - 'prediction': { 'result': …, 'confidence': […] }
        - 'formatted_date': e.g. '25th May'
    """
    API_URL = 'https://api.football-data.org/v4'
    headers = {'X-Auth-Token': API_TOKEN}

    # 1) Get all La Liga matches to discover the highest matchday
    resp_all = requests.get(f"{API_URL}/competitions/2014/matches", headers=headers)
    if resp_all.status_code != 200:
        return [], None

    all_matches = resp_all.json().get("matches", [])
    # Only consider those with a non‐null matchday
    matchday_numbers = [m["matchday"] for m in all_matches if m.get("matchday") is not None]
    if not matchday_numbers:
        return [], None

    latest_md = max(matchday_numbers)

    # 2) Now query specifically for that latest matchday
    resp_md = requests.get(f"{API_URL}/competitions/2014/matches?matchday={latest_md}", headers=headers)
    if resp_md.status_code != 200:
        return [], latest_md

    md_matches = resp_md.json().get("matches", [])
    result_list = []

    for m in md_matches:
        # Filter only Primera Division (in case the endpoint returns other comps)
        if m.get("competition", {}).get("name") != "Primera Division":
            continue

        # Prepare score object (full‐time). If not available yet, default to dashes.
        ft = m.get("score", {}).get("fullTime", {"home": "-", "away": "-"})

        # Run your existing prediction logic
        pred, conf = predict_match(m["homeTeam"]["name"], m["awayTeam"]["name"])
        # Build the fixture‐dict exactly as front end expects:
        fixture = {
            "utcDate": m["utcDate"],
            "homeTeam": {"name": m["homeTeam"]["name"]},
            "awayTeam": {"name": m["awayTeam"]["name"]},
            "score": {"fullTime": {"home": ft.get("home"), "away": ft.get("away")}},
            "prediction": {
                "result": pred,            # e.g. "Home Win" / "Draw" / "Away Win"
                "confidence": conf or []   # your model’s [0.7,0.15,0.15], etc.
            },
            "formatted_date": format_date_nice(m["utcDate"])
        }
        result_list.append(fixture)

    return result_list, latest_md


# === API Routes ===
@app.route('/api/teams', methods=['GET'])
def api_teams():
    return jsonify(STATIC_TEAMS)

@app.route('/api/fixtures/next/<int:team_id>', methods=['GET'])
def api_next(team_id):
    key = f"{team_id}_next"
    if key in CACHE and is_cache_valid(CACHE[key]['time'], seconds=300):
        return jsonify(CACHE[key]['data'])
    headers = {'X-Auth-Token': API_TOKEN}
    res = requests.get(f"{API_URL}/teams/{team_id}/matches?status=SCHEDULED&limit=5", headers=headers)
    fixtures = []
    if res.status_code == 200:
        for m in res.json().get('matches', []):
            if m['competition']['name'] != 'Primera Division': continue
            pred, proba = predict_match(m['homeTeam']['name'], m['awayTeam']['name'])
            fixtures.append({
                'utcDate': m['utcDate'],
                'home': m['homeTeam']['name'],
                'away': m['awayTeam']['name'],
                'prediction': {
                    'result': pred,
                    'confidence': proba
                }
            })
        CACHE[key] = {'data': fixtures, 'time': datetime.now()}
    return jsonify(fixtures)

@app.route('/api/fixtures/last/<int:team_id>', methods=['GET'])
def api_last(team_id):
    key = f"{team_id}_last"
    if key in CACHE and is_cache_valid(CACHE[key]['time'], seconds=300):
        return jsonify(CACHE[key]['data'])
    headers = {'X-Auth-Token': API_TOKEN}
    res = requests.get(f"{API_URL}/teams/{team_id}/matches?status=FINISHED&limit=5", headers=headers)
    results = []
    if res.status_code == 200:
        for m in sorted(res.json().get('matches', []), key=lambda x: x['utcDate'], reverse=True):
            if m['competition']['name'] != 'Primera Division': continue
            ft = m['score']['fullTime']
            pred, proba = predict_match(m['homeTeam']['name'], m['awayTeam']['name'])
            results.append({
                'utcDate': m['utcDate'],
                'home': m['homeTeam']['name'],
                'away': m['awayTeam']['name'],
                'score': {'home': ft['home'], 'away': ft['away']},
                'prediction': {
                    'result': pred,
                    'confidence': proba
                }
            })
        CACHE[key] = {'data': results, 'time': datetime.now()}
    return jsonify(results)


@app.route('/api/fixtures/matchday', methods=['GET'])
def api_matchday():
    # This calls your existing helper:
    fixtures, matchday_num = get_latest_matchday_fixtures()
    # Return both the matchday number and the array of fixture objects
    return jsonify({
        "matchday": matchday_num,
        "fixtures": fixtures
    })


if __name__ == '__main__':
    app.run(debug=True)
