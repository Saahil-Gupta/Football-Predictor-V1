import os
from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import requests
import joblib
from datetime import datetime
import numpy as np
import unicodedata
import random

# === Load Environment ===
load_dotenv()
API_TOKEN = os.getenv('FOOTBALL_API_KEY')
API_URL = 'https://api.football-data.org/v4'
CACHE = {}

# === Flask App Init ===
app = Flask(__name__, static_folder='frontend_back/dist', static_url_path='')
CORS(app)

# === Load Models for Both Leagues ===
MODELS = {
    "laliga": {
        "model": joblib.load("match_predictor_advanced.pkl"),
        "encoder": joblib.load("team_label_encoder.pkl"),
        "strengths": joblib.load("team_strengths.pkl")
    },
    "prem": {
        "model": joblib.load("epl_match_predictor_advanced.pkl"),
        "encoder": joblib.load("epl_team_label_encoder.pkl"),
        "strengths": joblib.load("epl_team_strengths.pkl")
    }
}

# === Team Mapping ===
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
    "Villarreal CF": "Villarreal",

    # Premier League
    "Arsenal": "Arsenal FC",
    "Aston Villa": "Aston Villa FC",
    "Bournemouth": "AFC Bournemouth",
    "Brentford": "Brentford FC",
    "Brighton": "Brighton & Hove Albion FC",
    "Burnley": "Burnley FC",
    "Cardiff": "Cardiff City FC",
    "Chelsea": "Chelsea FC",
    "Crystal Palace": "Crystal Palace FC",
    "Everton": "Everton FC",
    "Fulham": "Fulham FC",
    "Huddersfield": "Huddersfield Town AFC",
    "Hull": "Hull City AFC",
    "Ipswich": "Ipswich Town FC",
    "Leeds": "Leeds United FC",
    "Leicester": "Leicester City FC",
    "Liverpool": "Liverpool FC",
    "Luton": "Luton Town FC",
    "Manchester City": "Manchester City FC",
    "Manchester United": "Manchester United FC",
    "Middlesbrough": "Middlesbrough FC",
    "Newcastle United": "Newcastle United FC",
    "Norwich": "Norwich City FC",
    "Nottingham Forest": "Nottingham Forest FC",
    "Sheffield United": "Sheffield United FC",
    "Southampton": "Southampton FC",
    "Stoke": "Stoke City FC",
    "Sunderland": "Sunderland AFC",
    "Swansea": "Swansea City AFC",
    "Tottenham": "Tottenham Hotspur FC",
    "Watford": "Watford FC",
    "West Bromwich Albion": "West Bromwich Albion FC",
    "West Ham": "West Ham United FC",
    "Wolverhampton Wanderers": "Wolverhampton Wanderers FC"
}

# === Static Team List ===
STATIC_TEAMS = [
    # La Liga
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

    # Premier League
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
    {"id": 340, "name": "Huddersfield Town AFC"},
    {"id": 322, "name": "Hull City AFC"},
    {"id": 68, "name": "Ipswich Town FC"}, 
    {"id": 341, "name": "Leeds United FC"},
    {"id": 338, "name": "Leicester City FC"},
    {"id": 64, "name": "Liverpool"},
    {"id": 389, "name": "Luton Town FC"},
    {"id": 65, "name": "Manchester City"},
    {"id": 66, "name": "Manchester United"},
    {"id": 343, "name": "Middlesbrough FC"},
    {"id": 67, "name": "Newcastle United"},
    {"id": 70, "name": "Norwich City FC"},
    {"id": 351, "name": "Nottingham Forest FC"},
    {"id": 356, "name": "Sheffield United FC"},
    {"id": 340, "name": "Southampton FC"},
    {"id": 236, "name": "Stoke City FC"},
    {"id": 71, "name": "Sunderland AFC"},
    {"id": 72, "name": "Swansea City AFC"},
    {"id": 73, "name": "Tottenham Hotspur"},
    {"id": 346, "name": "Watford FC"},
    {"id": 74, "name": "West Bromwich Albion"},
    {"id": 563, "name": "West Ham United FC"},
    {"id": 76, "name": "Wolverhampton Wanderers"}
]

# === Utility Functions ===
def normalize_team_name(name):
    mapped = TEAM_NAME_MAP.get(name, name)
    return unicodedata.normalize("NFKD", mapped).encode("ASCII", "ignore").decode("utf-8").strip()

def predict_match(home_team, away_team):
    home = normalize_team_name(home_team)
    away = normalize_team_name(away_team)

    league = None
    if home in MODELS["laliga"]["strengths"] and away in MODELS["laliga"]["strengths"]:
        league = "laliga"
    elif home in MODELS["prem"]["strengths"] and away in MODELS["prem"]["strengths"]:
        league = "prem"
    else:
        return None, None

    h = MODELS[league]["strengths"][home]
    a = MODELS[league]["strengths"][away]

    score = (h['offense_strength'] - a['defense_weakness']) - (a['offense_strength'] - h['defense_weakness'])
    total = score + random.uniform(-0.1, 0.1)

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

# === API Endpoints ===
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

@app.route('/api/teams', methods=['GET'])
def api_teams():
    return jsonify(STATIC_TEAMS)

@app.route('/api/fixtures/next/<int:team_id>', methods=['GET'])
def api_next(team_id):
    league = request.args.get('league', 'laliga')
    key = f"{team_id}_next_{league}"
    if key in CACHE and is_cache_valid(CACHE[key]['time'], seconds=300):
        return jsonify(CACHE[key]['data'])
    headers = {'X-Auth-Token': API_TOKEN}
    res = requests.get(f"{API_URL}/teams/{team_id}/matches?status=SCHEDULED&limit=5", headers=headers)
    fixtures = []
    if res.status_code == 200:
        for m in res.json().get('matches', []):
            if league == 'laliga' and m['competition']['code'] != 'PD': continue
            if league == 'prem' and m['competition']['code'] != 'PL': continue
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
    league = request.args.get('league', 'laliga')
    key = f"{team_id}_last_{league}"
    if key in CACHE and is_cache_valid(CACHE[key]['time'], seconds=300):
        return jsonify(CACHE[key]['data'])
    headers = {'X-Auth-Token': API_TOKEN}
    res = requests.get(f"{API_URL}/teams/{team_id}/matches?status=FINISHED&limit=5", headers=headers)
    results = []
    if res.status_code == 200:
        for m in sorted(res.json().get('matches', []), key=lambda x: x['utcDate'], reverse=True):
            if league == 'laliga' and m['competition']['code'] != 'PD': continue
            if league == 'prem' and m['competition']['code'] != 'PL': continue
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
