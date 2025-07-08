import asyncio
import pandas as pd
from understat import Understat
import aiohttp

SEASON = 2025  # Update this for the desired season

async def fetch_xg_data():
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        matches = await understat.get_league_results("La liga", SEASON)

        data = []
        for match in matches:
            home_team = match["h"]["title"]
            away_team = match["a"]["title"]
            home_goals = int(match["goals"]["h"])
            away_goals = int(match["goals"]["a"])
            home_xg = float(match["xG"]["h"])
            away_xg = float(match["xG"]["a"])

            data.append({
                "date": match["datetime"][:10],  # format: YYYY-MM-DD
                "home_team": home_team,
                "away_team": away_team,
                "home_xg": home_xg,
                "away_xg": away_xg,
                "score": f"{home_goals}-{away_goals}"
            })

        df = pd.DataFrame(data)
        filename = f"la_liga_schedule_{SEASON}_{SEASON+1}.csv"
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"CSV created: {filename}")

if __name__ == "__main__":
    asyncio.run(fetch_xg_data())
