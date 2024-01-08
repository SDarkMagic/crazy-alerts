import os
import pathlib
from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix
import titanfall

cert_dir = pathlib.Path(__file__).parent.parent / 'certs'
app = Flask(__name__)
#app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
queue = None
tf = titanfall.TF(queue)
ws =SocketIO(app)


@app.route('/audio')
def audio():
    return render_template('audio.html')

@app.route('/js/<path:file_name>')
def js_files(file_name):
    return send_from_directory(pathlib.Path(__file__).parent / 'js', file_name)

@app.route('/songs/<path:file_name>')
def music_files(file_name):
    return send_from_directory(pathlib.Path(__file__).parent.parent / 'songs', file_name)

@app.route('/music')
def music():
    return render_template('music.html')

@app.route('/titanfall-callback', methods=['POST'])
def titanfall_callback():
    if (request.method != 'POST'):
        return "Request was not a POST request"
    return tf.post(request)

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
    global tf
    queue = q
    tf.queue = q
    q.put(ws)
    if (os.getenv('environment') == 'dev'):
        ws.run(app, host='0.0.0.0', debug=True, port=3000, allow_unsafe_werkzeug=True)
    else:
        ws.run(app, host='0.0.0.0', debug=False, port=3000, allow_unsafe_werkzeug=True, ssl_context=(str((cert_dir / 'cert.crt').absolute()), str((cert_dir / 'key_decrypt.key').absolute())))