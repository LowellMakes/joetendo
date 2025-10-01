#!/usr/bin/env python3

import logging
import os
import select
import signal
import subprocess
import sys
import time

from .common import ex, main_wrapper, get_configuration, switch_keymap
from .valve import get_executable, load_or_fetch_info, guess_thumbnail


LOG = logging.getLogger('vent')


def xfconf_query(channel, prop, value=None):
    if value:
        ex(
            "xfconf-query",
            "--create",
            "--type", "string",
            "-c", channel,
            "-p", prop,
            "-s", value,
        )
    else:
        ex(
            "xfconf-query",
            "-c", channel,
            "-p", prop,
            "-r",
        )


def xfterm_query(prop, value=None):
    xfconf_query("xfce4-terminal", prop, value)


def remove_splash():
    xfconf_query("xfce4-terminal", "/background-image-file")
    xfconf_query("xfce4-terminal", "/background-mode")
    xfconf_query("xfce4-terminal", "/background-image-style")


def do_configure_splash(img):
    xfconf_query("xfce4-terminal", "/font-name", "Monospace Bold 20")
    if img:
        xfterm_query("/background-image-file", img)
        xfterm_query("/background-mode", "TERMINAL_BACKGROUND_IMAGE")
        xfterm_query("/background-image-style", "TERMINAL_BACKGROUND_STYLE_SCALED")
    else:
        remove_splash()


def configure_splash(img):
    try:
        do_configure_splash(img)
    except FileNotFoundError:
        LOG.warning("Could not change terminal background. Is xfconf-query installed?")


def launch_wait(cfg, appID):
    subprocess.run("clear", check=False, shell=True)

    info = load_or_fetch_info(appID, cfg.cache_dir)
    executable = get_executable(info)
    game = info['vdf'].get('common', {}).get('name', '?????')

    img = os.path.join(cfg.cache_dir, str(appID), "raw_page_background.jpg")
    if not os.path.exists(img):
        img = guess_thumbnail(cfg.cache_dir, str(appID))
    configure_splash(img)

    LOG.info(
        "Launching appID=%s; game='%s'; executable='%s';",
        appID, game, executable
    )

    print(f"Launching {game} ... ..", end='')
    sys.stdout.flush()

    ex("steam", f"steam://rungameid/{appID}")
    LOG.debug("Waiting for executable '%s'", executable)

    pid = None
    for i in range(60):
        ret = subprocess.run(
            f"ps ax -o pid,comm | grep -i {executable}",
            shell=True,
            capture_output=True,
            check=False,
        )
        if ret.returncode:
            print(f"\b\b{60-i:2d}", end='')
            sys.stdout.flush()
            time.sleep(1)
            continue

        pid = int(ret.stdout.decode().strip().split(" ")[0])
        LOG.debug(
            "Executable running: appID=%s; game='%s'; executable='%s'; pid=%s",
            appID,
            game,
            executable,
            pid,
        )
        break
    else:
        print("")
        LOG.error(
            "Timed out waiting for appID=%s; game='%s'; executable='%s'",
            appID,
            game,
            executable,
        )
        exc = Exception(
            f"Timed out waiting for {appID=} {game=} {executable=}"
        )
        exc.add_note(
            "System may be in an unusable state. "
            "Consider using the reset kill switch?"
        )
        raise exc

    print("")
    print("Game now running! Please enjoy =^_^=")

    pidfd = os.pidfd_open(pid)

    def handler(_sig, _frame):
        LOG.debug("SIGTERM received from exit button")
        LOG.debug("Forwarding SIGTERM to game process")
        signal.pidfd_send_signal(pidfd, signal.SIGTERM)

    signal.signal(signal.SIGTERM, handler)

    while True:
        ret = select.select([pidfd], [], [])
        LOG.debug(
            "appID=%s; game='%s'; executable='%s'; pid=%s closed, exiting vent launcher",
            appID,
            game,
            executable,
            pid,
        )
        LOG.debug("ret=%s", str(ret))
        print("Game closed, returning you to the menu (｡･ω･｡)ﾉ♡")
        break


def do_launch(cfg, appID, keymap):
    switch_keymap(cfg.active_keymap, cfg.default_keymap, keymap)
    try:
        launch_wait(cfg, appID)
    finally:
        switch_keymap(cfg.active_keymap, cfg.default_keymap, cfg.default_keymap)
        remove_splash()


def do_main():
    cfg = get_configuration()
    os.makedirs(cfg.keymap_dir, exist_ok=True)

    appID = sys.argv[1]
    keymap = cfg.keymap_dir.joinpath(f"{appID}.conf")

    LOG.debug("> vent %s", appID)
    LOG.debug("    appID=%s", appID)
    LOG.debug("    steam_root=%s", cfg.steam_dir)
    LOG.debug("    active_keymap=%s", cfg.active_keymap)
    LOG.debug("    default_keymap=%s", cfg.default_keymap)
    LOG.debug("    keymap=%s", keymap)

    do_launch(cfg, appID, keymap)


def main():
    main_wrapper(do_main)


if __name__ == '__main__':
    main()
