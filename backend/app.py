import os
from dotenv import load_dotenv
from flask import Flask, render_template, request
import sqlite3
import requests
from datetime import datetime, timedelta
load_dotenv()

app = Flask(__name__)


API_TOKEN = os.getenv('FOOTBALL_API_KEY')
print("Loaded API Token:", API_TOKEN)
if not API_TOKEN:
    raise ValueError("API Token not found. Please set the FOOTBALL_API_KEY environment variable.")
API_URL = 'https://api.football-data.org/v4'
CACHE = {}

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
    url = f"{API_URL}/competitions/2014/matches"  # all matches
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        matches = response.json().get("matches", [])
        if not matches:
            return [], None
        latest_matchday = max(m["matchday"] for m in matches if m["matchday"] is not None)

        # Now fetch full set of matches for that matchday
        url_latest = f"{API_URL}/competitions/2014/matches?matchday={latest_matchday}"
        r2 = requests.get(url_latest, headers=headers)
        if r2.status_code == 200:
            week_matches = r2.json().get("matches", [])
            for m in week_matches:
                m["formatted_date"] = format_date_nice(m["utcDate"])
            week_matches.sort(key=lambda x: x["utcDate"], reverse=True)
            CACHE[key] = {"data": week_matches, "time": datetime.utcnow(), "matchday": latest_matchday}
            return week_matches, latest_matchday
    return [], None


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

    return render_template('index.html', teams=teams, selected_team=selected_team,
                           next_fixture=next_fixture, last_fixtures=last_fixtures,
                           matchday_fixtures=matchday_fixtures, latest_matchday=latest_matchday)

if __name__ == '__main__':
    app.run(debug=True)