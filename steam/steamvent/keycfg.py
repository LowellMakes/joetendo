import argparse
from pathlib import Path
import json
from xml.etree import ElementTree

import sdl2

# Default KEYD configuration
#
# This dict maps keyd aliases to keyd keycode names.
#
# Any 'keyd' name is valid as a value, however not all values are
# necessarily mapped for EmulationStation and RetroArch; multimedia keys
# and non-en_US keys have a higher likelihood of being unmapped. Only
# unshifted keys are mapped, e.g. 'semicolon' is available but 'colon'
# is not.
#
# In effect, this mapping symbolically defines the relationship between
# standard arcade control layouts and the actual keypresses we have
# configured them to generate. This mapping uses, as much as possible,
# the "default" or "expected" keypresses that MAME is configured to
# recognize, which in turn are also the default keybinds configured for
# the IPAC device.
#
# It is used first and foremost to generate /etc/keyd/common, which
# assigns aliases to raw keypresses, e.g. pressing "z" will register a
# press for "p1_5".
#
# Further below, these alias names are used to define the relationship
# between the arcade layout and emulated controller buttons for both
# EmulationStation and RetroArch.
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


# Default EmulationStation configuration for player 1.
#
# Maps ES control names (left) to Keyd aliases (right).
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

# Default EmulationStation configuration for player 2.
default_es_config_p2 = {
    'up':            'p2_up',
    'down':          'p2_down',
    'left':          'p2_left',
    'right':         'p2_right',
    'b':             'p2_1',
    'a':             'p2_2',
    'rightshoulder': 'p2_3',
    'y':             'p2_4',
    'x':             'p2_5',
    'leftshoulder':  'p2_6',
    'righttrigger':  'p2_7',
    'lefttrigger':   'p2_8',
    #
    'select':        'p2_coin',
    'start':         'p2_start',
}


default_retroarch_config = {
    "input_player1_b": "p1_1",
    "input_player1_a": "p1_2",
    "input_player1_r": "p1_3",
    "input_player1_y": "p1_4",
    "input_player1_x": "p1_5",
    "input_player1_l": "p1_6",
    "input_player1_r2": "p1_7",
    "input_player1_l2": "p1_8",
    "input_player1_select": "p1_coin",
    "input_player1_start": "p1_start",
    "input_player1_up": "p1_up",
    "input_player1_down": "p1_down",
    "input_player1_left": "p1_left",
    "input_player1_right": "p1_right",

    "input_player2_b": "p2_1",
    "input_player2_a": "p2_2",
    "input_player2_r": "p2_3",
    "input_player2_y": "p2_4",
    "input_player2_x": "p2_5",
    "input_player2_l": "p2_6",
    "input_player2_r2": "p2_7",
    "input_player2_l2": "p2_8",
    "input_player2_select": "p2_coin",
    "input_player2_start": "p2_start",
    "input_player2_up": "p2_up",
    "input_player2_down": "p2_down",
    "input_player2_left": "p2_left",
    "input_player2_right": "p2_right",
}


def config_to_SDL2(mapping, data):
    config = {}
    for es_name, keyd_alias in mapping.items():
        if keyd_alias not in keycfg:
            raise Exception(f"Unknown keyd_alias '{keyd_alias}'")
        keyd_name = keycfg[keyd_alias]
        if keyd_name not in data:
            raise Exception(f"Unmapped keyd keycode '{keyd_name}' not in SDL mapping file")

        config[es_name] = getattr(sdl2, data[keyd_name])
    return config


def config_to_retroarch(translation_map):
    config = {}
    for ra_name, keyd_alias in default_retroarch_config.items():
        if keyd_alias not in keycfg:
            raise Exception(f"Unknown keyd_alias '{keyd_alias}'")
        keyd_name = keycfg[keyd_alias]
        if keyd_name not in translation_map:
            raise Exception(f"keyd keycode '{keyd_name}' not in RetroArch mapping file")

        config[ra_name] = translation_map[keyd_name]
    return config


def generate_es_config():
    here = Path(__file__).parent

    with open(here.joinpath("keymap.json"), "r") as file:
        data = json.load(file)

    p1_config = config_to_SDL2(default_es_config, data)
    # p2_config = config_to_SDL2(default_es_config_p2, data)

    print('<?xml version="1.0"?>')
    print('<inputList>')

    print('    <inputConfig type="keyboard" deviceName="Keyboard" deviceGUID="-1">')
    for es_name, sdl_value in p1_config.items():
        print(f'        <input name="{es_name}" type="key" id="{sdl_value}" value="1" />')
    print('    </inputConfig>')

    # print('    <inputConfig type="keyboard" deviceName="Keyboard" deviceGUID="-1">')
    # for es_name, sdl_value in p2_config.items():
    #     print(f'        <input name="{es_name}" type="key" id="{sdl_value}" value="1" />')
    # print('    </inputConfig>')

    print('</inputList>')


def generate_retroarch_config():
    here = Path(__file__).parent

    with open(here.joinpath("retroarch_map.json"), "r") as file:
        data = json.load(file)

    config = config_to_retroarch(data)

    for key, value in config.items():
        print(f'{key} = "{value}"')


def main():
    parser = argparse.ArgumentParser(
        description="Generate keybinding configurations for various programs from a central configuration file",
        epilog="Have a nice day! =^_^=",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-es', '--emulationstation', default=False, help="Generate EmulationStation configuration", action="store_true")
    group.add_argument('-ra', '--retroarch', default=False, help="Generate RetroArch configuration", action="store_true")

    args = parser.parse_args()

    if args.emulationstation:
        generate_es_config()
    elif args.retroarch:
        generate_retroarch_config()


if __name__ == '__main__':
    main()
