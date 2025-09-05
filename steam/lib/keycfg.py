from pathlib import Path
import json
from xml.etree import ElementTree

import sdl2

keycfg = {
    'p1_up':    'up',
    'p1_down':  'down',
    'p1_left':  'left',
    'p1_right': 'right',
    'p1_1':     'leftcontrol',
    'p1_2':     'leftalt',
    'p1_3':     'space',
    'p1_4':     'leftshift',
    'p1_5':     'z',
    'p1_6':     'x',
    'p1_7':     'c',
    'p1_8':     'v',
    'p1_a':     'p',
    'p1_b':     'enter',
    'p1_coin':  '5',
    'p1_start': '1',

    'p2_up':    'r',
    'p2_down':  'f',
    'p2_left':  'd',
    'p2_right': 'g',
    'p2_1':     'a',
    'p2_2':     's',
    'p2_3':     'q',
    'p2_4':     'w',
    'p2_5':     'i',
    'p2_6':     'k',
    'p2_7':     'j',
    'p2_8':     'l',
    'p2_a':     'tab',
    'p2_b':     'esc',
    'p2_coin':  '6',
    'p2_start': '2',
}


default_es_config = {
    'up':            'p1_up',
    'down':          'p1_down',
    'left':          'p1_left',
    'right':         'p1_right',
    'b':             'p1_1',
    'a':             'p1_2',
    'rightshoulder': 'p1_3',
    'y':             'p1_4',
    'x':             'p1_5',
    'leftshoulder':  'p1_6',
    'righttrigger':  'p1_7',
    'lefttrigger':   'p1_8',
    'hotkeyenable':  'p1_a',
    'select':        'p1_coin',
    'start':         'p1_start',
}


def generate_es_config():
    here = Path(__file__).parent

    with open(here.joinpath("keymap.json"), "r") as file:
        data = json.load(file)

    config = {}
    for es_name, keyd_alias in default_es_config.items():
        if keyd_alias not in keycfg:
            raise Exception(f"Unknown keyd_alias '{keyd_alias}'")
        keyd_name = keycfg[keyd_alias]
        if keyd_name not in data:
            raise Exception(f"Unmapped keyd keycode '{keyd_name}' not in SDL mapping file")

        config[es_name] = getattr(sdl2, data[keyd_name])

    print('<?xml version="1.0"?>')
    print('<inputList>')
    print('    <inputConfig type="keyboard" deviceName="Keyboard" deviceGUID="-1">')
    for es_name, sdl_value in config.items():
        print(f'        <input name="{es_name}" type="key" id="{sdl_value}" value="1" />')
    print('    </inputConfig>')
    print('</inputList>')


if __name__ == '__main__':
    generate_es_config()
