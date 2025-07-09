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
    {"id": 88,  "name": "Levante UD"},
    {"id": 285, "name": "Elche CF"},
    {"id": 1048, "name": "Real Oviedo"},

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
    {"id": 341, "name": "Leeds United FC"},
    {"id": 64, "name": "Liverpool"},
    {"id": 65, "name": "Manchester City"},
    {"id": 66, "name": "Manchester United"},
    {"id": 67, "name": "Newcastle United"},
    {"id": 351, "name": "Nottingham Forest FC"},
    {"id": 71, "name": "Sunderland AFC"},
    {"id": 73, "name": "Tottenham Hotspur"},
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


# def get_latest_matchday_fixtures(league='laliga'):
#     """
#         Queries the Football‐Data API to find the highest (latest) matchday in the specified league,
#         then returns a tuple: (list_of_fixture_dicts, latest_matchday_number).
#         Each fixture dict includes:
#         - 'utcDate'
#         - 'homeTeam': { 'name': … }
#         - 'awayTeam': { 'name': … }
#         - 'score': { 'fullTime': { 'home': X, 'away': Y } }
#         - 'prediction': { 'result': …, 'confidence': […] }
#         - 'formatted_date': e.g. '25th May'
#     """
#     # Map league to competition ID
#     competition_id = {
#         'laliga': '2014',  # La Liga
#         'epl': 'PL'     # Premier League
#     }.get(league)

#     if not competition_id:
#         return [], None  # Invalid league

#     API_URL = f'https://api.football-data.org/v4/competitions/{competition_id}/matches'
#     headers = {'X-Auth-Token': API_TOKEN}

#     # 1) Get all matches to discover the highest matchday
#     resp_all = requests.get(API_URL, headers=headers)
#     if resp_all.status_code != 200:
#         return [], None

#     all_matches = resp_all.json().get("matches", [])
#     # Only consider those with a non‐null matchday
#     matchday_numbers = [m["matchday"] for m in all_matches if m.get("matchday") is not None]
#     if not matchday_numbers:
#         return [], None

#     latest_md = max(matchday_numbers)

#     # 2) Now query specifically for that latest matchday
#     # resp_md = requests.get(f"{API_URL}?matchday={latest_md}", headers=headers)
#     # if resp_md.status_code != 200:
#     #     return [], latest_md

#     # md_matches = resp_md.json().get("matches", [])
#     md_matches = [m for m in all_matches if m.get("matchday") == latest_md]
#     print("Total matches fetched:", len(all_matches))
#     print("Sample match:", all_matches[0] if all_matches else "No matches found")

#     matchday_numbers = [m.get("matchday") for m in all_matches if m.get("matchday") is not None]
#     print("Matchdays found:", matchday_numbers)
#     result_list = []

#     for m in md_matches:
#         # Filter only matches for the specified league
#         if league == 'laliga' and m.get("competition", {}).get("code") != "PD":
#             continue
#         if league == 'prem' and m.get("competition", {}).get("code") != "PL":
#             continue

#         # Prepare score object (full‐time). If not available yet, default to dashes.
#         ft = m.get("score", {}).get("fullTime", {})
#         home_goals = ft.get("home") if ft.get("home") is not None else "-"
#         away_goals = ft.get("away") if ft.get("away") is not None else "-"


#         # Run your existing prediction logic
#         pred, conf = predict_match(m["homeTeam"]["name"], m["awayTeam"]["name"])
#         # Build the fixture‐dict exactly as front end expects:
#         fixture = {
#             "utcDate": m["utcDate"],
#             "homeTeam": {"name": m["homeTeam"]["name"]},
#             "awayTeam": {"name": m["awayTeam"]["name"]},
#             "score": {
#             "fullTime": {
#                 "home": home_goals,
#                 "away": away_goals
#             }},

#             "prediction": {
#                 "result": pred,            # e.g. "Home Win" / "Draw" / "Away Win"
#                 "confidence": conf or []   # your model’s [0.7,0.15,0.15], etc.
#             },
#             "formatted_date": format_date_nice(m["utcDate"])
#         }
#         result_list.append(fixture)

#     return result_list, latest_md

import requests

def get_latest_matchday_fixtures(league='laliga'):
    """
    Fetches fixtures for the current matchday of the ongoing/upcoming season
    in the specified league. Each fixture includes:
    - 'utcDate'
    - 'homeTeam': { 'name': … }
    - 'awayTeam': { 'name': … }
    - 'score': { 'fullTime': { 'home': X, 'away': Y } }
    - 'prediction': { 'result': …, 'confidence': […] }
    - 'formatted_date': e.g. '25th May'
    """
    # Map league to competition ID
    competition_id = {
        'laliga': '2014',  # La Liga
        'epl': 'PL'        # Premier League
    }.get(league)

    if not competition_id:
        return [], None  # Invalid league

    headers = {'X-Auth-Token': API_TOKEN}

    # 1) Get current matchday from competition info
    comp_url = f"https://api.football-data.org/v4/competitions/{competition_id}"
    comp_resp = requests.get(comp_url, headers=headers)
    if comp_resp.status_code != 200:
        return [], None

    current_md = comp_resp.json().get("currentSeason", {}).get("currentMatchday")
    if not current_md:
        return [], None

    # 2) Fetch matches for the current matchday
    API_URL = f"https://api.football-data.org/v4/competitions/{competition_id}/matches?matchday={current_md}"
    matches_resp = requests.get(API_URL, headers=headers)
    if matches_resp.status_code != 200:
        return [], current_md

    matches = matches_resp.json().get("matches", [])
    result_list = []

    for m in matches:
        # Filter by league code just to be safe
        if league == 'laliga' and m.get("competition", {}).get("code") != "PD":
            continue
        if league == 'epl' and m.get("competition", {}).get("code") != "PL":
            continue

        ft = m.get("score", {}).get("fullTime", {})
        home_goals = ft.get("home") if ft.get("home") is not None else "-"
        away_goals = ft.get("away") if ft.get("away") is not None else "-"

        # Prediction
        pred, conf = predict_match(m["homeTeam"]["name"], m["awayTeam"]["name"])

        fixture = {
            "utcDate": m["utcDate"],
            "homeTeam": {"name": m["homeTeam"]["name"]},
            "awayTeam": {"name": m["awayTeam"]["name"]},
            "score": {
                "fullTime": {
                    "home": home_goals,
                    "away": away_goals
                }
            },
            "prediction": {
                "result": pred,
                "confidence": conf or []
            },
            "formatted_date": format_date_nice(m["utcDate"])
        }

        result_list.append(fixture)

    return result_list, current_md



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


# =========== EPL TEAMS =======================
@app.route('/api/epl/teams', methods=['GET'])
def api_epl_teams():
    epl_teams = [team for team in STATIC_TEAMS if team['name'] in [t['name'] for t in STATIC_TEAMS[20:]]]
    return jsonify(epl_teams)


# ======== LALIGA TEAMS =========================
@app.route('/api/laliga/teams', methods=['GET'])
def api_teams():
    laliga_teams = [team for team in STATIC_TEAMS if team['name'] in [t['name'] for t in STATIC_TEAMS[:20]]]
    return jsonify(laliga_teams)


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


@app.route('/api/fixtures/matchday', methods=['GET'])
def api_matchday():
    # Get the league from query parameters, default to 'laliga'
    league = request.args.get('league', 'laliga')
    
    # Call the helper function with the specified league
    fixtures, matchday_num = get_latest_matchday_fixtures(league=league)
    
    # Return both the matchday number and the array of fixture objects
    return jsonify({
        "matchday": matchday_num,
        "fixtures": fixtures
    })

if __name__ == '__main__':
    app.run(debug=True)




# @app.route('/api/epl/fixtures/next/<int:team_id>', methods=['GET'])
# def api_epl_next(team_id):
#     key = f"{team_id}_next_prem"
#     if key in CACHE and is_cache_valid(CACHE[key]['time'], seconds=300):
#         return jsonify(CACHE[key]['data'])
#     headers = {'X-Auth-Token': API_TOKEN}
#     res = requests.get(f"{API_URL}/teams/{team_id}/matches?status=SCHEDULED&limit=5", headers=headers)
#     fixtures = []
#     if res.status_code == 200:
#         for m in res.json().get('matches', []):
#             if m['competition']['code'] != 'PL': continue
#             pred, proba = predict_match(m['homeTeam']['name'], m['awayTeam']['name'])
#             fixtures.append({
#                 'utcDate': m['utcDate'],
#                 'home': m['homeTeam']['name'],
#                 'away': m['awayTeam']['name'],
#                 'prediction': {
#                     'result': pred,
#                     'confidence': proba
#                 }
#             })
#         CACHE[key] = {'data': fixtures, 'time': datetime.now()}
#     return jsonify(fixtures)


# @app.route('/api/epl/fixtures/last/<int:team_id>', methods=['GET'])
# def api_epl_last(team_id):
#     key = f"{team_id}_last_prem"
#     if key in CACHE and is_cache_valid(CACHE[key]['time'], seconds=300):
#         return jsonify(CACHE[key]['data'])
#     headers = {'X-Auth-Token': API_TOKEN}
#     res = requests.get(f"{API_URL}/teams/{team_id}/matches?status=FINISHED&limit=5", headers=headers)
#     results = []
#     if res.status_code == 200:
#         for m in sorted(res.json().get('matches', []), key=lambda x: x['utcDate'], reverse=True):
#             if m['competition']['code'] != 'PL': continue
#             ft = m['score']['fullTime']
#             pred, proba = predict_match(m['homeTeam']['name'], m['awayTeam']['name'])
#             results.append({
#                 'utcDate': m['utcDate'],
#                 'home': m['homeTeam']['name'],
#                 'away': m['awayTeam']['name'],
#                 'score': {'home': ft['home'], 'away': ft['away']},
#                 'prediction': {
#                     'result': pred,
#                     'confidence': proba
#                 }
#             })
#         CACHE[key] = {'data': results, 'time': datetime.now()}
#     return jsonify(results)