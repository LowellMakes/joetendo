#!/usr/bin/env python3

from dataclasses import dataclass
import datetime
import logging
from logging.handlers import SysLogHandler
import os
from pathlib import Path
import shlex
import subprocess


LOG = logging.getLogger('vent')


def ex(*args, check=True, capture_output=False):
    cmd = " ".join(shlex.quote(arg) for arg in args)
    LOG.debug("exec> %s", cmd)
    try:
        result = subprocess.run(args, check=check, capture_output=capture_output)
        return result
    except subprocess.CalledProcessError:
        LOG.exception("subprocess failed")
        raise


def have_binary(name):
    res = ex("which", name, check=False)
    return bool(res.returncode == 0)


def mklink(source, dest):
    ex("ln", "-f", "-s", str(dest), str(source))


def configure_logging():
    address = ''
    if os.path.exists('/dev/log'):
        address = '/dev/log'
    elif os.path.exists('/var/run/syslog'):
        address = '/var/run/syslog'

    if address:
        syslog = SysLogHandler(address=address)
    else:
        syslog = SysLogHandler()

    syslog.setLevel(logging.DEBUG)
    syslog.setFormatter(
        logging.Formatter("%(name)s: %(message)s")
    )

    LOG.setLevel(logging.DEBUG)
    LOG.addHandler(syslog)


def main_wrapper(callback):
    configure_logging()

    try:
        callback()
    except Exception as exc:
        LOG.exception("Unhandled exception in main()")
        print("""
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣴⠶⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⡿⠃⠀⠀⠀⠀⠀⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣘⣿⡧⠤⠤⠤⠖⠛⠋⠉⠙⢦⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⡴⠚⠋⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢯⠙⠦⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣤⡤⢤⣴⣞⣹⡿⠶⣶⠀⠀⠀⢰⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠈⠛⢦⣀⣀⣴⠟⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢼⠁⢹⠁⣽⠏⠀⣠⣤⡴⠃⠀⠀⠀⣼⡀⠀⠀⠀⣠⠀⣤⣄⠀⠀⢸⠀⠀⠀⠀⠀⠓⢾⡁⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⡴⣶⡶⣿⣇⠟⠀⠉⠀⢰⠏⠀⣤⣀⠀⠀⣸⠻⣷⠀⠀⣰⣿⣴⡯⠊⠀⢀⣿⣰⡄⠀⠶⢼⡄⠀⠙⡄⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡴⠛⣉⣠⣾⣿⡇⠞⠃⠀⠀⠀⠀⢾⡆⢰⣿⠁⢀⡼⠣⢤⣿⣤⠞⠁⢹⣯⣧⠀⠀⡼⠉⢿⣧⠀⠀⠀⢻⡄⠀⢹⡄⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢀⣾⣋⣴⣶⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠘⣷⣾⣧⡴⠋⢀⡴⠚⠛⠛⢶⡦⣼⣿⣿⣀⡾⠁⠀⠘⣿⣆⠀⠀⠘⡇⠀⠀⢧⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⢹⣿⡃⠀⠀⠘⣆⠚⢉⡷⠀⢱⡄⠙⣿⡿⠁⢤⣤⣰⣿⣿⠃⠀⠀⣿⠀⠀⢸⡄⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠻⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⣾⣿⡇⠀⠀⠀⠉⠙⢉⣥⠴⠚⠀⠀⠘⢧⠀⢸⢧⣼⣿⣿⡇⠀⠀⣾⠀⠀⢸⣽⣆⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⣿⣿⡟⠀⠀⠀⠀⠀⠀⢀⣼⠏⣿⢧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣿⠿⢏⣿⡇⠀⣰⣯⣴⠀⢸⠀⠙⠧⠀⠀⠀⠀
⠀⠀⠀⠐⢤⡀⠀⠀⠀⠀⠀⠀⠘⢛⠟⠀⠀⠀⠀⠀⢀⣰⣿⠅⠀⠙⣿⠳⠤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣺⠏⣇⣰⡟⣿⣿⣴⡟⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠉⠢⡀⠀⠀⠀⠀⡰⠋⠀⠀⠀⠀⠀⢀⣾⡿⠁⠀⠀⠀⠸⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⢀⣿⢏⣼⢯⣿⡟⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠈⠳⣄⢀⡞⠁⠀⠀⠀⠀⠀⢀⣾⣿⣷⣠⠀⠀⠀⢸⡿⠀⠀⣖⠓⠒⠲⠤⠤⢄⣀⣀⠀⠀⠀⠀⢸⣿⠈⣿⡿⢡⣞⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣨⠏⠀⠀⠀⠀⠀⠀⢀⡞⣉⣈⢻⣿⣷⣤⣄⣼⡇⠀⠀⠙⠋⠉⠉⠉⠓⠒⠲⢭⣽⣲⣆⠀⣼⣿⠀⢿⡇⠀⠈⠓⢤⡀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣰⠃⠀⠀⠀⠀⠀⠀⢀⡾⠋⠉⠉⠉⠛⢿⣿⣿⣿⡟⢶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢈⣩⡾⠟⠉⠀⢸⣷⡀⠀⠀⠀⠙⢦⡀⠀⠀⠀⠀⠀
⣆⡀⠀⠀⠀⠀⠀⣰⠃⠀⠀⠀⠀⠀⠀⢀⣾⠀⣀⡀⠀⠀⠀⠈⠻⣿⣿⡛⠲⢭⣗⠦⣤⣀⠀⣀⣠⣤⣴⣺⣿⣏⡀⡀⠀⢀⣴⣿⣷⡄⠀⡀⠀⠀⠙⢦⡀⠀⠀⠀
⠀⠙⠳⢄⡀⠀⢠⠇⠀⠀⠀⠀⠀⠀⠀⡼⠉⠉⠲⢯⠑⠆⠀⠀⠀⠙⣿⣷⡀⠀⠈⠉⠻⢿⣿⣝⡻⣿⣿⣷⣄⠙⠿⢷⡶⠟⠙⣇⡙⢮⣀⠘⠲⢄⡀⠀⠙⣆⠀⠀
⠀⠀⠀⠀⠙⠢⡾⠀⠀⠀⠀⠀⠀⠀⡼⠃⠀⠀⠀⠈⢳⠀⠀⠀⠀⠀⢹⣿⣇⢀⣠⠤⠚⣿⣿⣿⣿⣶⣭⣿⣿⣧⡀⠀⠀⠀⠀⠸⣽⡀⠈⠉⠛⠓⠒⠂⠀⠘⣧⠀
⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠇⠀⠀⠀⠀⢸⣿⣿⣿⡅⠀⣼⡏⢻⣏⠻⣷⣍⡙⠛⣿⣿⡆⠀⠀⠀⠀⢻⡇⠀⠀⠀⠀⠀⠀⠀⠈⢸⡆
⠀⠀⠀⠀⡀⠒⠷⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣴⣯⣸⠀⠀⠀⢀⣸⣿⣿⣿⢻⡴⣿⣅⣸⣿⡄⠈⠛⠿⣾⡿⣿⡿⣆⢀⠀⠀⠘⣿⠀⠀⠀⠀⠀⢀⣀⡴⠚⠁
⠀⠀⠀⠀⠙⠢⣄⡈⠉⠙⢷⡒⠒⠛⠻⣯⣭⣭⡿⢻⠟⠁⠀⠀⠠⣾⣿⣿⣿⣿⣄⡻⣬⣿⣿⣿⣦⣤⣤⣤⣤⣤⣘⣷⡘⣿⠀⠀⣴⡗⠒⠒⠒⠉⠉⠉⠁⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠙⢷⡀⠀⠙⠶⢤⣀⡀⠙⠦⣄⡀⠀⠀⣀⣀⣴⣿⣿⣿⣿⣿⣿⣷⣦⣦⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⣷⠾⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢦⣀⠀⠀⠀⠈⠙⠲⠤⣍⣉⠉⠀⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⡂⠰⣄⠀⠀⠀⠲⢤⣀⡀⠉⠉⠒⢢⣨⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⢹⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠓⠬⠵⠤⠄⣀⣀⣘⣚⣶⠤⠒⠉⠀⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠈⢻⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠁⠀⠀⠀⠀⠀⠘⣷⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠈⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡏⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠘⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⠤⠤⠤⠤⠤⠤⠤⠤⢀⣀⡠⢿⣮⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠘⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⠤⠖⠂⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⡴⠞⠉⠀⠘⣿⢃⣿⣿⣿⣿⣿⣿⣿⠟⢿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠹⡀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢀⣀⠄⠀⠀⢀⣀⣀⣀⣀⠠⠀⢀⣀⣀⣠⢴⠿⠟⠋⠀⠀⠀⠀⠀⠀⢹⡇⢹⣿⣿⣿⣿⣿⣿⣤⣾⣿⣿⣿⣿⣿⣿⣿⡀⠀⠀⠀⣧⠀⠀⠀⠀⠀⠀⠀⠀""")

        print("")
        print("Oww...!!")
        print(f"{type(exc).__name__}: {str(exc)}")
        print("")
        print(
            "This event has been logged. If you have admin access, type "
            "`journalctl --identifier=vent --since=today` to review the logs."
        )
        print("")
        print(
            "Please report this failure on the Arcade gaming basecamp, "
            "or send a mail to gaming@lowellmakes.com."
        )
        print("Thank you, and sorry for the inconvenience!")
        print("")
        print("You may want to press the reset switch inside the control deck.")
        print("The control panel lifts up, and there's a pink box with a black button on it.")
        print("Push it to reset the system.")
        print("")

        now = datetime.datetime.now()
        later = now + datetime.timedelta(minutes=3)
        while datetime.datetime.now() < later:
            remaining = later - datetime.datetime.now()
            print("\r" + "Return to menu in " + str(remaining)[3:], end='')
        raise
    finally:
        print("")


@dataclass
class Configuration:
    user: str
    home_dir: Path
    retropie_dir: Path
    steam_dir: Path
    game_dir: Path
    keymap_dir: Path
    active_keymap: Path
    default_keymap: Path
    keyd_config: Path
    es_config: Path
    autostart_config: Path


def get_configuration():
    user = os.environ.get(
        "__user",
        os.environ.get(
            "SUDO_USER",
            os.environ.get(
                "USER",
                None
            )
        )
    )

    if not user:
        # TODO: use 'whoami'?
        raise Exception("Failed to determine who is running this script. Who are you?")

    home = Path(os.path.expanduser(f"~{user}"))
    rp_root = home.joinpath("RetroPie")
    steam_root = rp_root.joinpath("steam")
    keymap_dir = steam_root.joinpath("keymaps")

    cfg = Configuration(
        user=user,
        home_dir=home,
        retropie_dir=rp_root,
        steam_dir=steam_root,
        game_dir=steam_root.joinpath("menu"),
        keymap_dir=keymap_dir,
        active_keymap=keymap_dir.joinpath("active.conf"),
        default_keymap=keymap_dir.joinpath("default.conf"),
        keyd_config=Path('/etc/keyd/default.conf'),
        es_config=Path('/etc/emulationstation/es_systems.cfg'),
        autostart_config=home.joinpath('.config/autostart/retropie.desktop'),
    )

    return cfg
