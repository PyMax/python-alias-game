import sqlite3
conn = sqlite3.connect('alias.db')
print ("Opened database successfully");

conn.execute('CREATE TABLE IF NOT EXISTS words(title_en TEXT, title_ru TEXT)')
print ("Table created successfully");
cur = conn.cursor()
try:
	with open('wordlist.txt', 'r') as wd:
		words = [l.rstrip() for l in wd]
	with open('translated_list.txt','r') as tr:
		trans = [t.rstrip() for t in tr]
	for i, w in enumerate(words):
		cur.execute("INSERT INTO words (title_en, title_ru) VALUES (?,?)",(w, trans[i]) )
	conn.commit()
	msg = "Records successfully added"
except:
	conn.rollback()
	msg = "error in insert operation"
	  
finally:
	print(msg)
	#query = cur.execute('select * from words').fetchall();
	conn.close()
	#print(query)