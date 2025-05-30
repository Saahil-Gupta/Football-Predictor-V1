import sqlite3

conn = sqlite3.connect('la_liga.db')
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    )
""")

teams = [
    (77, "Athletic Club"),
    (78, "Club Atlético de Madrid"),
    (79, "CA Osasuna"),
    (80, "RCD Espanyol de Barcelona"),
    (81, "FC Barcelona"),
    (82, "Getafe CF"),
    (86, "Real Madrid CF"),
    (87, "Rayo Vallecano de Madrid"),
    (89, "RCD Mallorca"),
    (90, "Real Betis Balompié"),
    (92, "Real Sociedad de Fútbol"),
    (94, "Villarreal CF"),
    (95, "Valencia CF"),
    (250, "Real Valladolid CF"),
    (263, "Deportivo Alavés"),
    (275, "UD Las Palmas"),
    (298, "Girona FC"),
    (558, "RC Celta de Vigo"),
    (559, "Sevilla FC"),
    (745, "CD Leganés")
]


cursor.executemany('INSERT OR IGNORE INTO teams (id, name) VALUES (?, ?)', teams)

conn.commit()
conn.close()