import twitchio
import random
import queue
import pathlib
import re
import time
import json
from twitchio.ext import commands

COOLDOWN = 10 # Amount of time in seconds before the sound can be triggered again

def load_config(path):
    SimpleAudio_template = {
        'name': '',
        'pattern': '',
        'cooldown': COOLDOWN,
        'isCaseSensitive': True
    }
    config_template = {
        'alerts': {
            'SimpleAudio': [],
            'CommandAudio': {}
        }
    }
    with open(path, 'rt') as raw:
        return json.loads(raw.read())

class AudioPlayer():
    def __init__(self, name, queue, pattern, cooldown=0, is_case_sensitive=False, file_probabilities={}):
        self._name = name
        self.queue = queue
        self.pattern = pattern
        self.cooldown = cooldown
        self.is_case_sensitive = is_case_sensitive
        self.probabilities = file_probabilities
        self.files = list((pathlib.Path(__file__).parent.parent / f'audio/{name}').rglob('*.wav'))
        self.last_call = time.time()

        if len(self.probabilities) > 0:
            total_weights = sum(self.probabilities.values())
            self.probabilities['play_silence'] = float(1 - total_weights)

        return

    def play_audio(self, file=None):
        if ((time.time() - self.last_call) > self.cooldown):
            try:
                ws = self.queue.get() # Try to get the websocked object from the queue to stream audio data to
            except queue.Empty:
                print('Error, queue was empty. Terminating...')
                return

            file_to_play = file

            if file_to_play == None:
                if len(self.probabilities) > 0:
                    file_to_play = pathlib.Path(f'{pathlib.Path(__file__).parent.parent}/audio/{self._name}/{random.choices(list(self.probabilities.keys()), weights=list(self.probabilities.values()))[0]}')
                else:
                    file_to_play = random.choice(self.files)
            self.last_call = time.time()

            if file_to_play.name == 'play_silence':
                self.queue.put(ws)
                return

            self.send_data_to_socket(ws, file_to_play, self._name)
            self.queue.put(ws) # Return the websocket to the queue after use so that other threads can use it
        return

    @staticmethod
    def send_data_to_socket(ws, file, name='external-function-call'):
        with open(file, 'rb') as raw:
            ws.emit('play-audio', (raw.read(), json.dumps({'name': name})))
        return

class HandlerCog(commands.Cog):
    def __init__(self, bot: commands.Bot, players: list):
        self.bot = bot
        self.players = players
        return

    @commands.Cog.event()
    async def event_message(self, msg):
        for player in self.players:
            regex_flags = []

            if player.is_case_sensitive != True:
                regex_flags.append(re.IGNORECASE)
            if player.is_case_sensitive != True:
                if (re.search(player.pattern, msg.content, re.IGNORECASE)):
                    player.play_audio()
                    break
            else:
                if (re.search(player.pattern, msg.content)):
                    player.play_audio()
                    break

class Bot(commands.Bot):
    def __init__(self, token, secret, channel, q):
        self.config = load_config(pathlib.Path(__file__).parent.parent / 'config.json')
        super().__init__(token=token, client_secret=secret, prefix='!', initial_channels=[channel])
        self.target_channel = channel
        self.queue = q
        self.initialize_external_configs()
        return

    def initialize_external_configs(self):
        alerts = self.config['alerts']
        players = []
        probabilities = {}
        for alert in alerts['SimpleAudio']:
            if 'isCaseSensitive' in alert.keys():
                caseSensitive = alert['isCaseSensitive']
            else:
                caseSensitive = False
            if 'probabilities' in alert.keys():
                probabilities = alert['probabilities']
            players.append(AudioPlayer(alert['name'], self.queue, alert['pattern'], alert['cooldown'], caseSensitive, probabilities))
        self.add_cog(HandlerCog(self, players))

    async def event_message(self, ctx):
        if ctx.content.startswith(self._prefix):
            command_audio = self.config['alerts']['CommandAudio']
            cmd = ctx.content.split(' ')[0].lstrip(self._prefix)
            try:
                path = command_audio[cmd]
            except KeyError:
                print(f'"{cmd}" is not a valid command')
                return
            try:
                ws = self.queue.get()
            except queue.Empty:
                return
            AudioPlayer.send_data_to_socket(ws, path, f'audio-commands-{cmd}')
            self.queue.put(ws)
        return

    async def event_ready(self):
        print(f'Successfully connected')