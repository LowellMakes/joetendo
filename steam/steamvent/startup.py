import sys
import time
import subprocess

from .common import ex, switch_keymap, get_configuration
from .lolfiglet import lolfiglet


def do_kiosk():
    proc = subprocess.Popen(
        ["steam", "-nochat", "-nopopup", "-silent"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        lolfiglet("SUPER JOETENDO")
        ex("emulationstation", "--force-kiosk", "--no-exit")
    finally:
        proc.terminate()


def kiosk():
    config = get_configuration()

    switch_keymap(
        config.active_keymap,
        config.default_keymap,
        config.default_keymap
    )

    try:
        do_kiosk()
    finally:
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
        "--hide-scrollbar",
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
