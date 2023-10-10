from flask import Flask, render_template, request, session, redirect,url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from datetime import datetime
from string import ascii_uppercase

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
socketio = SocketIO(app)

rooms = {}

def generate_code(length):
	while True:
		code = ""
		for _ in range(length):
			code += random.choice(ascii_uppercase)
		if code not in rooms:
			break

	return code

@app.route("/", methods=['GET', 'POST'])
def index():
	session.clear()
	if request.method == "POST":
		name = request.form.get("name")
		room_code = request.form.get("room_code")
		join = request.form.get("join", False)
		create = request.form.get("create", False)

		if not name:
			return render_template('index.html', error="Please enter your name.", room_code=room_code, name=name)

		if join != False and not room_code:
			return render_template('index.html', error="Please enter Room Code.", room_code=room_code, name=name)

		room = room_code
		if create != False:
			room = generate_code(4)
			rooms[room]={'members':0, 'message':[]}

		elif room_code not in rooms:
			return render_template('index.html', error="Room is not exist.", room_code=room_code, name=name)

		session['room'] = room
		session['name'] = name
		return redirect(url_for("room"))

	return render_template('index.html')


@app.route("/room")
def room():
	room = session.get('room')
	name = session.get('name')

	if room is None or name is None or room not in rooms:
		return redirect(url_for("index"))

	return render_template('room.html', room=room, messages=rooms[room]['message'])

@socketio.on("message")
def message(data):
	room = session.get('room')
	name = session.get('name')
	time = datetime.today().strftime('%I:%M')

	if room not in rooms:
		return None

	content = {'name':name, 'message':data['data'], 'time':time}
	send(content, to=room)
	rooms[room]['message'].append(content)





@socketio.on("connect")
def connect(auth):
	room = session.get("room")
	name = session.get("name")

	if not room and not name:
		return redirect(url_for("index"))

	if room not in rooms:
		leave_room(room)
		return redirect(url_for("index"))

	join_room(room)
	time =datetime.today().strftime('%I:%M')
	send({'name':f"<span class='active-user'>{name}</span>", 'message':'has been entered.', 'time':time}, to=room)
	rooms[room]['members'] += 1
	# print(f"{name} join {room}")


@socketio.on("disconnect")
def disconnect():
	room = session.get("room")
	name = session.get("name")
	leave_room(room)

	if room in rooms:
		rooms[room]['members'] -= 1
		if rooms[room]['members'] <= 0:
			del rooms[room]

	time = datetime.today().strftime('%I:%M')
	send({'name':f"<span class='deactive-user'>{name}</span>", 'message':'has been left.', 'time':time}, to=room)
	# print(f"{name} left {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True)