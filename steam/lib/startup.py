import sys
import time
import subprocess

from common import ex, switch_keymap, get_configuration
from lolfiglet import lolfiglet


def kiosk():
    config = get_configuration()

    switch_keymap(
        config.active_keymap,
        config.default_keymap,
        config.default_keymap
    )

    proc = subprocess.Popen(
        ["steam", "-nochat", "-nopopup", "-silent"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    lolfiglet("NOW LOADING")

    #print("Launching emulationstation ...")
    ex("emulationstation", "--force-kiosk", "--no-exit")

    switch_keymap(
        config.active_keymap,
        config.default_keymap,
        config.default_keymap
    )


def kiosk_launcher():
    ex(
        "xfce4-terminal",
        "--fullscreen",
        "--maximize",
        "--hide-menubar",
        "--hide-borders",
        "--hide-toolbar",
        "-x",
        "kiosk"
    )


def main():
    if sys.argv[1] == 'launcher':
        kiosk_launcher()
    elif sys.argv[1] == 'kiosk':
        kiosk()


if __name__ == '__main__':
    main()
