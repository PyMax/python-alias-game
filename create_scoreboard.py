import sqlite3
conn = sqlite3.connect('alias.db')
print("Opened database successfully");
conn.execute("DROP TABLE IF EXISTS scoreboard");
conn.execute('CREATE TABLE IF NOT EXISTS scoreboard(id INTEGER PRIMARY KEY,user_id INTEGER, room VARCHAR(8),player_name VARCHAR(255),score INTEGER)')
print("Table created successfully");

#query = conn.execute("SELECT * FROM scoreboard").fetchall()
#print(query)