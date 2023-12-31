import asyncio

from pybambu import BambuClient

import json
import os
from datetime import datetime

import telebot
from decouple import config

tb_token = config('TB_TOKEN')
chat_id = config('CHAT_ID')


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


class MyBambuClient(BambuClient):
    _gcode_state = "unknown"
    _print_error = 0
    _name = None

    def __init__(self, device_type: str, serial: str, host: str, username: str, access_code: str, name: str):
        self._name = name
        super().__init__(device_type, serial, host, username, access_code)

    def event_handler(self, event):
        # print(event)
        info = self.get_device().info
        if self._gcode_state != info.gcode_state or self._print_error != info.print_error:
            mes = f'{self._name}\n{info.gcode_state} {info.gcode_file} {info.print_percentage}%\n{info.print_error}'

            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "\n", mes)
            bot = telebot.TeleBot(tb_token)
            bot.send_message(chat_id, mes)
            self._gcode_state = info.gcode_state
            self._print_error = info.print_error


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
