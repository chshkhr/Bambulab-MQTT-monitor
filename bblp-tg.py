import asyncio

from pybambu import BambuClient

import json
import os
from datetime import datetime

import telebot
from decouple import config

from flask import Flask, render_template, url_for, send_from_directory
from flask_socketio import SocketIO
from engineio.async_drivers import gevent

tb_token = config('TB_TOKEN')
chat_id = config('CHAT_ID')
http_port = int(config('HTTP_PORT'))

# Create a new Flask app instance
app = Flask(__name__, template_folder='./templates', static_folder='./static')

# Set up the SocketIO server
socketio = SocketIO(app, async_mode='gevent')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


connected_count = 0

# Handle new messages from SocketIO clients
@socketio.on('connect')
def on_connect():
    global connected_count
    connected_count += 1
    print(f'Client connected: {connected_count}')


@socketio.on('disconnect')
def on_disconnect():
    global connected_count
    connected_count -= 1
    print(f'Client disconnected: {connected_count}')


cfg = [
    {
        'name': 'Printer 1',
        'device_type': "P1P",
        'serial': "01S00C000000000",
        'host': "192.168.0.15",
        'access_code': "12345678",
    },
    {
        'name': 'Printer 2',
        'device_type': "P1S",
        'serial': "01P00A000000000",
        'host': "192.168.0.17",
        'access_code': "12345678",
    },
]

work_dir = os.getcwdb().decode("utf-8")


def cfg_save():
    fn = os.path.join(work_dir, 'cfg.json')
    with open(fn, 'w') as fp:
        json.dump(cfg, fp, indent=4)


def cfg_load():
    global cfg
    fn = os.path.join(work_dir, 'cfg.json')
    if os.path.exists(fn):
        with open(fn, 'r') as fp:
            cfg = json.load(fp)
    else:
        cfg_save()


cfg_load()


def text_to_id(text):
    # Replace spaces with underscores
    text = text.replace(" ", "_")

    # Remove any non-alphanumeric characters except for underscores
    text = ''.join(e for e in text if e.isalnum() or e == '_')

    # Ensure that the resulting ID starts with a letter
    if not text[0].isalpha():
        text = "x" + text

    return text


class MyBambuClient(BambuClient):
    _gcode_state = "unknown"
    _print_error = 0
    _name = None

    def __init__(self, device_type: str, serial: str, host: str, username: str, access_code: str, name: str):
        self._name = name
        super().__init__(device_type, serial, host, username, access_code)

    def event_handler(self, event):
        global connected_count
        # print(event)
        info = self.get_device().info

        if connected_count > 0:
            socketio.emit('mqtt-update', {
                'id': text_to_id(self._name),
                'name': self._name,
                'gcode_state': info.gcode_state,
                'print_error': 'ERROR!' if info.print_error else '',
                'gcode_file': info.gcode_file,
                'print_percentage': info.print_percentage,
                'remaining_time': info.remaining_time,
                'end_time':  info.end_time
            }, namespace='/')

        if self._gcode_state != info.gcode_state or self._print_error != info.print_error:
            mes = f'{self._name}\n{info.gcode_state} {info.gcode_file} {info.print_percentage}%\n{info.print_error}'

            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\n", mes)
            bot = telebot.TeleBot(tb_token)
            bot.send_message(chat_id, mes)
            self._gcode_state = info.gcode_state
            self._print_error = info.print_error


if __name__ == '__main__':
    for printer in cfg:
        client = MyBambuClient(
            device_type=printer['device_type'],
            serial=printer['serial'],
            host=printer['host'],
            username="bblp",
            name=printer['name'],
            access_code=printer['access_code']
        )


        async def listen():
            await client.connect(callback=client.event_handler)


        asyncio.run(listen())

    # Start the Flask server and the MQTT client
    socketio.run(app, debug=False, host='0.0.0.0', port=http_port, use_reloader=False)
