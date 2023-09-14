from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
queue = None
ws =SocketIO(app)

@app.route('/audio')
def audio():
    return render_template('audio.html')

@app.route('/')
def index():
    return render_template('index.html')

@ws.on('shutdown')
def shutdown():
    data = queue.get()
    if data == 'kill':
        ws.stop()
    return

def start(q):
    global queue
    queue = q
    q.put(ws)
    ws.run(app, host='0.0.0.0', debug=True, port=3001)