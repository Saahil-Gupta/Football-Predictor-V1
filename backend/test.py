import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
import requests
import joblib
from datetime import datetime
import numpy as np
from pymongo import MongoClient
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Flask app init
app = Flask(__name__)
CORS(app)

# API and DB config
API_TOKEN = os.getenv('FOOTBALL_API_KEY')
URI_MONGO = os.getenv('URI_MONGO')
DEFAULT_SEASON = os.getenv('DEFAULT_SEASON', '2024_2025')

if not API_TOKEN:
    raise ValueError("API Token not found. Please set FOOTBALL_API_KEY in .env.")
if not URI_MONGO:
    raise ValueError("MongoDB URI not found. Please set MONGO_URI in .env.")

# Connect to MongoDB
mongo_client = MongoClient(URI_MONGO)
mongo_db = mongo_client['LaLiga']


# right after mongo_db = mongo_client['LaLiga']
print("⚙️ DEFAULT_SEASON:", DEFAULT_SEASON)
print("⚙️ Collections in LaLiga:", mongo_db.list_collection_names())
print("⚙️ Documents in", DEFAULT_SEASON, ":", mongo_db[DEFAULT_SEASON].count_documents({}))


# Load ML model and encoder
en_model = joblib.load("match_predictor_advanced.pkl")
le_team = joblib.load("team_label_encoder.pkl")

# Team name mapping: API -> model/DB names
TEAM_NAME_MAP = {
    "FC Barcelona": "Barcelona",
    "Real Madrid CF": "Real Madrid",
    "Club Atlético de Madrid": "Atlético Madrid",
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
    "Deportivo Alavés": "Alavés",
    "Girona FC": "Girona",
    "Sevilla FC": "Sevilla",
    "CD Leganés": "Leganés",
    "UD Las Palmas": "Las Palmas",
    "Real Valladolid CF": "Valladolid"
}


# Static list of La Liga teams with their API-Football IDs and model names
STATIC_TEAMS = [
    {"id": 81,  "name": "Barcelona"},
    {"id": 86,  "name": "Real Madrid"},
    {"id": 78,  "name": "Atlético Madrid"},
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
    {"id": 263, "name": "Alavés"},
    {"id": 298, "name": "Girona"},
    {"id": 559, "name": "Sevilla"},
    {"id": 745, "name": "Leganés"},
    {"id": 275, "name": "Las Palmas"},
    {"id": 250, "name": "Valladolid"},
]



API_URL = 'https://api.football-data.org/v4'
CACHE = {}


    # """
    # Fetch team list from MongoDB collection for DEFAULT_SEASON:
    #   Collection name: teams_<season> (e.g. teams_2023_2024)
    # Returns list of tuples: (id, name)
    # """
    # coll_name = f"teams_{DEFAULT_SEASON}"
    # collection = mongo_db[coll_name]
    # docs = collection.find({}, {'_id': 0, 'id': 1, 'name': 1})
    # # sort by name
    # teams = sorted([(d['id'], d['name']) for d in docs], key=lambda x: x[1])
    # return teams
def get_teams():
    """
    Return the static list of La Liga teams.
    """
    return STATIC_TEAMS

def format_date_nice(utc_string):
    dt = datetime.strptime(utc_string, "%Y-%m-%dT%H:%M:%SZ")
    day = dt.day
    suffix = ( 'th' if 11 <= day <= 13 else {1:'st',2:'nd',3:'rd'}.get(day%10, 'th') )
    return f"{day}{suffix} {dt.strftime('%B')}"


def predict_match(home_team, away_team):
    # Map API names to model names
    home_team = TEAM_NAME_MAP.get(home_team, home_team)
    away_team = TEAM_NAME_MAP.get(away_team, away_team)
    if home_team not in le_team.classes_ or away_team not in le_team.classes_:
        print("[MAPPING ERROR]", home_team, away_team)
        return None, None
    # Encode and predict
    h = le_team.transform([home_team])[0]
    a = le_team.transform([away_team])[0]
    X = np.array([[0, 0, h, a] + [0]*11])
    proba = en_model.predict_proba(X)[0]
    pred = en_model.predict(X)[0]
    return pred, proba


def is_cache_valid(timestamp, seconds=60):
    return (datetime.today() - timestamp).total_seconds() < seconds


def get_next_fixture(team_id):
    key = f"{team_id}_next"
    if key in CACHE and is_cache_valid(CACHE[key]['time'], seconds=300):
        return CACHE[key]['data']
    headers = {'X-Auth-Token': API_TOKEN}
    url = f"{API_URL}/teams/{team_id}/matches?status=SCHEDULED&limit=5"
    res = requests.get(url, headers=headers)
    fixtures = []
    if res.status_code == 200:
        for m in res.json().get('matches', []):
            if m['competition']['name'] != 'Primera Division':
                continue
            pred, proba = predict_match(m['homeTeam']['name'], m['awayTeam']['name'])
            fixtures.append({
                'utcDate': m['utcDate'],
                'home': m['homeTeam']['name'],
                'away': m['awayTeam']['name'],
                'prediction': f"{['Home','Draw','Away'][pred]} ({max(proba)*100:.1f}%)" if pred is not None else None
            })
        CACHE[key] = {'data': fixtures, 'time': datetime.today()}
    return fixtures


def get_last_fixtures(team_id):
    key = f"{team_id}_last"
    if key in CACHE and is_cache_valid(CACHE[key]['time'], seconds=300):
        return CACHE[key]['data']
    headers = {'X-Auth-Token': API_TOKEN}
    url = f"{API_URL}/teams/{team_id}/matches?status=FINISHED&limit=5"
    res = requests.get(url, headers=headers)
    results = []
    if res.status_code == 200:
        for m in sorted(res.json().get('matches', []), key=lambda x: x['utcDate'], reverse=True):
            if m['competition']['name'] != 'Primera Division':
                continue
            results.append({
                'utcDate': m['utcDate'],
                'home': m['homeTeam']['name'],
                'away': m['awayTeam']['name'],
                'score': f"{m['score']['fullTime']['home']}–{m['score']['fullTime']['away']}"
            })
        CACHE[key] = {'data': results, 'time': datetime.today()}
    return results


# @app.route('/', methods=['GET', 'POST'])
# def index():
#     teams = get_teams()
#     selected = None
#     next_fx = []
#     last_fx = []
#     if request.method == 'POST':
#         selected = int(request.form['team'])
#         next_fx = get_next_fixture(selected)
#         last_fx = get_last_fixtures(selected)
#     return render_template('index.html', teams=teams, selected=selected,
#                            next_fixture=next_fx, last_fixtures=last_fx)


# JSON endpoints for React frontend
@app.route('/api/teams', methods=['GET'])
def api_teams():
    return jsonify(get_teams())

@app.route('/api/fixtures/next/<int:team_id>', methods=['GET'])
def api_next(team_id):
    return jsonify(get_next_fixture(team_id))

@app.route('/api/fixtures/last/<int:team_id>', methods=['GET'])
def api_last(team_id):
    return jsonify(get_last_fixtures(team_id))


TEAM_LOOKUP = { t['id']: t['name'] for t in STATIC_TEAMS }

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """
    Expects JSON:
      { "homeId": 81, "awayId": 86 }
    Returns:
      { "result": 0, "confidence": [0.7,0.1,0.2] }
    """
    data = request.get_json()
    home_id = data.get('homeId')
    away_id = data.get('awayId')

    home_name = TEAM_LOOKUP.get(home_id)
    away_name = TEAM_LOOKUP.get(away_id)
    if not home_name or not away_name:
        return jsonify({'error': 'Unknown team IDs'}), 400

    pred, proba = predict_match(home_name, away_name)
    if pred is None:
        return jsonify({'error': 'Prediction unavailable'}), 500

    return jsonify({
        'result': int(pred),
        'confidence': proba
    })


if __name__ == '__main__':
    app.run(debug=True)
