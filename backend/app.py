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

if __name__ == '__main__':
    app.run(debug=True)
