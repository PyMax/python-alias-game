from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO, emit
import random
from string import ascii_uppercase
from uuid import uuid4

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app)

rooms = {}


def generate_unique_code(length):
	while True:
		code = ""
		for _ in range(length):
			code += random.choice(ascii_uppercase)

		if code not in rooms:
			break

	return code


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
			room = generate_unique_code(6)
			rooms[room] = {"members": 0, "messages": []}
		elif code not in rooms:
			return render_template("home.html", error="Room does not exist.", code=code, name=name)

		session["room"] = room
		session["name"] = name
		session["uid"] = uuid4()
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
	if room is None or room not in rooms or room.lower() != room_id:
		return redirect(url_for("home"))
	return render_template("game.html", code=room)


@app.route('/word')
def get_word():
	room = session.get("room")
	if room is None or room not in rooms:
		return redirect(url_for("home"))
	wordlist = [word.split() for word in open('wordlist.txt') ]
	if "words" not in rooms[room].keys():
		rooms[room]["words"] = []
	word = generate_word(wordlist, room)
	return word


def generate_word(wordlist, room):
	word = random.choice(wordlist)[0]
	if word not in rooms[room]['words']:
		rooms[room]['words'].append(word)
		return word
	else:
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
	print(f"{session.get('name')} said: {data['data']}")


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
	send({"name": name, "message": "has entered the room"}, to=room)
	rooms[room]["members"] += 1
	print(f"{name} joined room {room}")


@socketio.on("disconnect")
def disconnect():
	room = session.get("room")
	name = session.get("name")
	leave_room(room)

	if room in rooms:
		rooms[room]["members"] -= 1
		if rooms[room]["members"] <= 0:
			del rooms[room]

	send({"name": name, "message": "has left the room"}, to=room)
	print(f"{name} has left the room {room}")


@socketio.on("startGame")
def startGame():
	room = session.get("room")
	timer = 120
	emit('start', {"timer": timer, "start": True})
	print("timer " + str(timer) + " send to room " + str(room))


@socketio.on("endGame")
def endGame():
	room = session.get("room")
	emit('end', {"timer": 0, "end": True})


if __name__ == "__main__":
	socketio.run(app, debug=True)
