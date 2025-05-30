import os
from dotenv import load_dotenv
from flask import Flask, render_template, request
import sqlite3
import requests
import joblib
from datetime import datetime
import numpy as np
import unicodedata
import pandas as pd
import random

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
    "Villarreal CF": "Villarreal"
}


# === Load Environment and App ===
load_dotenv()
app = Flask(__name__)
API_TOKEN = os.getenv("FOOTBALL_API_KEY")
API_URL = 'https://api.football-data.org/v4'
CACHE = {}

# === Load Models ===
model = joblib.load("match_predictor_advanced.pkl")
le_team = joblib.load("team_label_encoder.pkl")
TEAM_STRENGTHS = joblib.load("team_strengths.pkl")

# === Helper Functions ===
def normalize_team_name(name):
    name = TEAM_NAME_MAP.get(name, name)
    return unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8").strip()


def get_teams():
    conn = sqlite3.connect('la_liga.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM teams ORDER BY name')
    teams = cursor.fetchall()
    conn.close()
    return teams

def is_cache_valid(cache_time, seconds=60):
    return (datetime.utcnow() - cache_time).total_seconds() < seconds

def format_date_nice(utc_string):
    dt = datetime.strptime(utc_string, "%Y-%m-%dT%H:%M:%SZ")
    day = dt.day
    suffix = lambda d: 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')
    return f"{day}{suffix(day)} {dt.strftime('%B')}"

def predict_match(home_team, away_team):
    home = normalize_team_name(home_team)
    away = normalize_team_name(away_team)

    if home not in TEAM_STRENGTHS or away not in TEAM_STRENGTHS:
        print(f"Unknown team(s): {home} / {away}")
        return None, None

    h = TEAM_STRENGTHS[home]
    a = TEAM_STRENGTHS[away]

    strength_score = (h["offense_strength"] - a["defense_weakness"]) - (a["offense_strength"] - h["defense_weakness"])
    noise = random.uniform(-0.1, 0.1)
    total_score = strength_score + noise

    if total_score > 0.15:
        return "Home Win", [0.75, 0.15, 0.1]
    elif total_score < -0.15:
        return "Away Win", [0.1, 0.15, 0.75]
    else:
        return "Draw", [0.25, 0.5, 0.25]


# === API Integration ===
def get_next_fixture(team_id):
    key = f"{team_id}_next"
    if key in CACHE and is_cache_valid(CACHE[key]["time"]):
        return CACHE[key]["data"]
    headers = {'X-Auth-Token': API_TOKEN}
    url = f"{API_URL}/teams/{team_id}/matches?status=SCHEDULED&limit=10"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        matches = response.json().get('matches', [])
        la_liga_matches = [m for m in matches if m["competition"]["name"] == "Primera Division"]
        for match in la_liga_matches:
            match["formatted_date"] = format_date_nice(match["utcDate"])
            pred, proba = predict_match(match["homeTeam"]["name"], match["awayTeam"]["name"])
            if pred:
                match["prediction"] = f"{pred} (Conf: {max(proba)*100:.1f}%)"
        first_match = la_liga_matches[0:1]
        CACHE[key] = {"data": first_match, "time": datetime.utcnow()}
        return first_match
    return []

def get_last_fixtures(team_id):
    key = f"{team_id}_last"
    if key in CACHE and is_cache_valid(CACHE[key]["time"]):
        return CACHE[key]["data"]
    headers = {'X-Auth-Token': API_TOKEN}
    url = f"{API_URL}/teams/{team_id}/matches?status=FINISHED&limit=20"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        matches = response.json().get('matches', [])
        la_liga_matches = [m for m in matches if m["competition"]["name"] == "Primera Division"]
        la_liga_matches.sort(key=lambda x: x["utcDate"], reverse=True)
        last_five = la_liga_matches[:5]
        for match in last_five:
            match["formatted_date"] = format_date_nice(match["utcDate"])
        CACHE[key] = {"data": last_five, "time": datetime.utcnow()}
        return last_five
    return []

def get_latest_matchday_fixtures():
    key = "latest_matchday"
    if key in CACHE and is_cache_valid(CACHE[key]["time"], seconds=600):
        return CACHE[key]["data"], CACHE[key]["matchday"]
    headers = {'X-Auth-Token': API_TOKEN}
    url = f"{API_URL}/competitions/2014/matches"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        matches = response.json().get("matches", [])
        if not matches:
            return [], None
        latest_matchday = max(m["matchday"] for m in matches if m["matchday"] is not None)
        url_latest = f"{API_URL}/competitions/2014/matches?matchday={latest_matchday}"
        r2 = requests.get(url_latest, headers=headers)
        if r2.status_code == 200:
            week_matches = r2.json().get("matches", [])
            for m in week_matches:
                m["formatted_date"] = format_date_nice(m["utcDate"])
                pred, proba = predict_match(m["homeTeam"]["name"], m["awayTeam"]["name"])
                if pred:
                    m["prediction"] = f"{pred} (Conf: {max(proba)*100:.1f}%)"
            week_matches.sort(key=lambda x: x["utcDate"], reverse=True)
            CACHE[key] = {"data": week_matches, "time": datetime.utcnow(), "matchday": latest_matchday}
            return week_matches, latest_matchday
    return [], None

# === Routes ===
@app.route('/', methods=['GET', 'POST'])
def index():
    teams = get_teams()
    selected_team = None
    next_fixture = []
    last_fixtures = []
    matchday_fixtures, latest_matchday = get_latest_matchday_fixtures()

    if request.method == 'POST':
        team_id = request.form.get('team')
        if team_id:
            selected_team = team_id
            next_fixture = get_next_fixture(team_id)
            last_fixtures = get_last_fixtures(team_id)

            if next_fixture:
                for match in next_fixture:
                    home = match["homeTeam"]["name"]
                    away = match["awayTeam"]["name"]
                    pred, _ = predict_match(home, away)
                    match["prediction"] = prediction_label(pred, home, away)

            if last_fixtures:
                for match in last_fixtures:
                    home = match["homeTeam"]["name"]
                    away = match["awayTeam"]["name"]
                    pred, _ = predict_match(home, away)
                    match["prediction"] = prediction_label(pred, home, away)

    if matchday_fixtures:
        for match in matchday_fixtures:
            home = match["homeTeam"]["name"]
            away = match["awayTeam"]["name"]
            pred, _ = predict_match(home, away)
            match["prediction"] = prediction_label(pred, home, away)

    return render_template('index.html',
                           teams=teams,
                           selected_team=selected_team,
                           next_fixture=next_fixture,
                           last_fixtures=last_fixtures,
                           matchday_fixtures=matchday_fixtures,
                           latest_matchday=latest_matchday)

def prediction_label(pred, home, away):
    if pred == "Home Win":
        return f"{home} to win"
    elif pred == "Away Win":
        return f"{away} to win"
    elif pred == "Draw":
        return "Draw"
    else:
        return "Unavailable"


# === Run Server ===
if __name__ == '__main__':
    app.run(debug=True)
