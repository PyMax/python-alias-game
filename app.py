from flask import Flask, render_template, request, session, redirect, url_for, g
from flask_socketio import join_room, leave_room, send, SocketIO, emit
import random
from string import ascii_uppercase
import sqlite3
from flask_caching import Cache

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app, cors_allowed_origins=['https://alias-qtcreator777.b4a.run','http://localhost:5000'])
cache = Cache(app, config={'CACHE_TYPE': "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300})
DATABASE = 'alias.db'

rooms = {}


def get_db():
	db = getattr(g, '_database', None)
	if db is None:
		db = g._database = sqlite3.connect(DATABASE)
	return db


def generate_unique_code(length):
	while True:
		code = ""
		for _ in range(length):
			code += random.choice(ascii_uppercase)

		if code not in rooms:
			break
	return code


@app.teardown_appcontext
def close_connection(exception):
	db = getattr(g, '_database', None)
	if db is not None:
		db.close()


@app.route("/", methods=["POST", "GET"])
def home():
	session.clear()
	if request.method == "POST":
		name = request.form.get("name")
		code = request.form.get("code")
		join = request.form.get("join", False)
		create = request.form.get("create", False)

		if not name:
			return render_template("home.html", error="Please enter a name.", code=code, name=name)

		if join != False and not code:
			return render_template("home.html", error="Please enter a room code.", code=code, name=name)

		room = code
		if create != False:
			room = generate_unique_code(8)
			rooms[room] = {"members": 0, "messages": [], 'words': set()}
		elif code not in rooms:
			return render_template("home.html", error="Room does not exist.", code=code, name=name)

		session["room"] = room
		session["name"] = name
		session['score'] = 0
		return redirect(url_for("game", room_id=room.lower()))

	return render_template("home.html")


@app.route("/room")
def room():
	room = session.get("room")
	if room is None or session.get("name") is None or room not in rooms:
		return redirect(url_for("home"))
	return render_template("room.html", code=room, messages=rooms[room]["messages"])


@app.route('/game/<string:room_id>')
def game(room_id):
	room = session.get("room")
	player_name = session.get("name")
	if room is None or room not in rooms or room.lower() != room_id:
		return redirect(url_for("home"))
	return render_template("game.html", code=room, player_name=player_name)


def get_word():
	room = session.get("room")
	if room is None or room not in rooms:
		return redirect(url_for("home"))
	wordlist = get_wordlist_db()
	word = generate_word(wordlist, room)
	return list(word)

@cache.cached()
def get_wordlist_db():
	return get_db().cursor().execute('SELECT title_en, title_ru FROM words').fetchall()

def generate_word(wordlist, room):
	word = random.choice(wordlist)
	if word and (word not in rooms[room]['words']):
		rooms[room]['words'].add(word)
		return word
	generate_word(wordlist, room)


@socketio.on("message")
def message(data):
	room = session.get("room")
	if room not in rooms:
		return

	content = {
		"name": session.get("name"),
		"message": data["data"]
	}
	send(content, to=room)
	rooms[room]["messages"].append(content)


@socketio.on("connect")
def connect(auth):
	room = session.get("room")
	name = session.get("name")
	if not room or not name:
		return
	if room not in rooms:
		leave_room(room)
		return

	join_room(room)
	rooms[room]["members"] += 1
	send({"name": name, "message": "has entered the room", "members" : rooms[room]["members"]}, to=room)
	session['user_id'] = rooms[room]["members"]
	set_user_score_record()


@socketio.on("disconnect")
def disconnect():
	room = session.get("room")
	name = session.get("name")
	members = 0
	leave_room(room)
	if room in rooms:
		rooms[room]["members"] -= 1
		members = rooms[room]["members"]
		if rooms[room]["members"] <= 0:
			del rooms[room]
			members = 0
	send({"name": name, "message": "has left the room", "members" : members}, to=room)


@socketio.on("startGame")
def startGame():
	if session.get('game_started'):
		return
	room = session.get("room")
	timer = 120
	session['game_started'] = True
	emit('start', {"timer": timer, "game_started": True}, to=room)
	startword = get_word()
	emit('word', {'word': startword[0], 'trans': startword[1]})


def set_user_score_record():
	room = session.get("room")
	name = session.get("name")
	score = session.get("score")
	user_id = session.get("user_id")
	score_exists = get_db().cursor().execute("SELECT 1 FROM scoreboard where room=? and user_id=?", [room, user_id]).fetchone()
	if not score_exists:
		get_db().cursor().execute("INSERT INTO scoreboard(user_id,room,player_name,score) VALUES(?, ?, ?, ?)", (user_id, room, name, score))
		get_db().commit()
		get_db().cursor().close()


def update_user_score():
	room = session.get("room")
	score = session.get("score")
	user_id = session.get("user_id")
	opponent_id = get_db().cursor().execute("SELECT user_id FROM scoreboard where room=? and user_id!=?", [room, user_id]).fetchone()
	if(opponent_id):
		get_db().cursor().execute("UPDATE scoreboard SET score=? WHERE room=? AND user_id=?", (score, room, opponent_id[0]))
		get_db().commit()
		get_db().cursor().close()


@socketio.on("endGame")
def endGame():
	session['game_started'] = False
	update_user_score()
	emit('end', {"timer": 0})


@socketio.on('getScore')
def get_score():
	room = session.get('room')
	scores = []
	scores_db = get_db().cursor().execute("SELECT user_id,player_name,score FROM scoreboard where room=?", [room]).fetchall()
	for score in scores_db:
		scores.append({'user_id': score[0], 'name': score[1], 'score': score[2]})
	get_db().cursor().close()
	emit('scoreboard', {'scores': scores})


@socketio.on('nextWord')
def nextWord(data):
	if not session.get('game_started'):
		return
	nextWord = get_word()
	if not data['skip']:
		session['score'] +=1
	emit('next_word', {'word': nextWord[0], 'trans': nextWord[1]})


if __name__ == "__main__":
	#port = int(os.environ.get('PORT', 5000))
	socketio.run(app, debug = False, port=5000)#, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
