from flask import Request
import queue
import json

class TF:
    def __init__(self, q: queue.Queue):
        self.queue = q

    def post(self, request: Request):
        query_params = request.args
        status = ""
        try:
            ws = self.queue.get() # Try to get the websocked object from the queue to stream audio data to
        except queue.Empty:
            print('Error, queue was empty. Terminating...')
            status = 500

        if 'positive' in query_params.keys():
            socket_event = 'increase-playback-rate'
        elif 'negative' in query_params.keys():
            socket_event = 'decrease-playback-rate'
        else:
            status = "Please include positive or negative"
        try:
            ws.emit(socket_event, (json.dumps({'modifier': query_params['modifier']})))
            status = "Sucess"
        except:
            status = 500
        self.queue.put(ws)
        return status