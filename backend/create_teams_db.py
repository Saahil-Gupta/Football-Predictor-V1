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
    (77, 'Athletic Club'),
    (78, 'Atlético Madrid'),
    (81, 'Barcelona'),
    (92, 'Cádiz'),
    (94, 'Celta Vigo'),
    (95, 'Elche'),
    (98, 'Espanyol'),
    (99, 'Getafe'),
    (102, 'Granada'),
    (104, 'Levante'),
    (108, 'Osasuna'),
    (110, 'Rayo Vallecano'),
    (113, 'Real Betis'),
    (114, 'Real Madrid'),
    (115, 'Real Sociedad'),
    (117, 'Sevilla'),
    (119, 'Valencia'),
    (120, 'Valladolid'),
    (121, 'Villarreal'),
    (86, 'Alavés')
]

cursor.executemany('INSERT OR IGNORE INTO teams (id, name) VALUES (?, ?)', teams)

conn.commit()
conn.close()