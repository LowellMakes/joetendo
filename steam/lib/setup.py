#!/usr/bin/env python3

from configparser import ConfigParser
import json
import logging
import os
from pwd import getpwnam
import shutil
import subprocess
import sys
from xml.etree import ElementTree

from common import ex, mklink, main_wrapper, have_binary, get_configuration
import keycfg

LOG = logging.getLogger('vent')

_HAVE_REQUESTS = False
try:
    import requests
    _HAVE_REQUESTS = True
except ModuleNotFoundError:
    pass

_HAVE_VDF = False
try:
    import vdf
    _HAVE_VDF = True
except ModuleNotFoundError:
    pass


def add_steam_system(config_path, steam_path):
    tree = ElementTree.parse(config_path)
    root = tree.getroot()

    if root.findall('system/name[.="steam"]'):
        return

    node = ElementTree.fromstring(f"""
    <system>
      <name>steam</name>
      <fullname>Steam</fullname>
      <path>{steam_path}</path>
      <extension>.sh</extension>
      <command>%ROM%</command>
      <platform>steam</platform>
      <theme>steam</theme>
    </system>
    """)

    root.append(node)
    ElementTree.indent(tree)
    tree.write(config_path)


def external_tool_setup():
    """
    Ensure that all external tooling required by the 'vent' launcher is installed and available.

    This includes:

    - keyd: the key remapping daemon
    - wget: only for downloading keyd sources, if necessary.
    - steam: the steam client itself, for downloading and launching steam games!
    - steamcmd: the command-line steam client, for downloading metadata
      and image assets necessary for launching the games from the
      command-line.
    - xfce4-terminal: A graphical terminal application capable of
      showing background images. This is used to show a splash screen
      image for the game as it is being launched, while also being able
      to show information about the launching process.
    - xfconf-query: A command line application used to change settings
      and configuration values for the xfce4-terminal application. Used
      to adjuts font size and set background images for the terminal
      during launch.
    - python3-requests: the 'requests' python library, used for fetching
      image assets from the valve servers.
    - python3-vdf: the 'vdf' python library, used for parsing Valve Data
      Format files, principally used to identify image assets and to
      identify the executable binary to launch a particular game. Also
      used to map steam appIDs to human-readable game names.

    All packages except for 'keyd' will be installed through apt/dpkg,
    using a .deb file for the steam client if necessary. This function
    avoids using the Ubuntu-packaged version of 'steam' because the snap
    version of steam has issues running Proton games, needed for
    launching Windows-only games through this Linux launcher.
    """

    if not have_binary("apt"):
        print(
            "This setup script is intended for apt-based systems only",
            file=sys.stderr
        )
        sys.exit(1)

    ran_update = False

    if not have_binary("keyd"):
        # We need to install keyd, the key remapper daemon that is
        # responsible for changing the keybinds of the control deck on a
        # per-game basis.

        if not have_binary("wget"):
            ex("apt", "update", "-y")
            ran_update = True
            ex("apt", "install", "-y", "wget")

        # keyd is not in the ubuntu repository, so we need to download
        # and compile from source. Use the latest release instead of the
        # latest dev snapshot and hope everything goes fine.
        try:
            ex(
                "wget",
                "https://api.github.com/repos/rvaiya/keyd/releases/latest",
                "-O",
                "keyd.json"
            )
            with open("keyd.json", "rb") as infile:
                data = json.load(infile)
                url = data['tarball_url']
            ex("wget", url, "-O", "keyd-latest.tar.gz")
            os.mkdir("keyd-latest")
            ex("tar", "zxf", "keyd-latest.tar.gz", "-C",
               "keyd-latest", "--strip-components", "1")
            ex("make", "-C", "keyd-latest/")
            ex("make", "install", "-C", "keyd-latest/")
        finally:
            ex("rm", "-f", "keyd.json")
            ex("rm", "-f", "keyd-latest.tar.gz")
            ex("rm", "-rf", "keyd-latest/")

    # A queue of packages to install all at once with 'apt'
    packages = []

    # steam and/or steamcmd may install their binary to /usr/games,
    # which is not typically part of the root user's PATH. Add it here
    # so we can detect its presence appropriately.
    os.environ['PATH'] = os.environ['PATH'] + ':/usr/games'

    if not have_binary("steam"):
        ex("wget", "https://repo.steampowered.com/steam/archive/stable/steam_latest.deb")
        packages.append("./steam_latest.deb")

    # Steam requires the user to interactively accept the steam license.
    # We've got better things to do with our life though,
    # so procedurally accept it for an unattended install.
    if not have_binary("steamcmd"):
        ex("add-apt-repository", "-y", "multiverse")
        subprocess.run('echo "steamcmd steam/license note" | debconf-set-selections', shell=True)
        subprocess.run('echo "steamcmd steam/purge note" | debconf-set-selections', shell=True)
        subprocess.run(
            'echo "steamcmd steam/question select I AGREE"'
            ' | debconf-set-selections',
            shell=True
        )
        ex("dpkg", "--add-architecture", "i386")
        packages.append("steamcmd")

    # xfconf-query *should* come along for the ride when we install xfce4-terminal.
    if not (have_binary("xfce4-terminal") or have_binary("xfconf-query")):
        packages.append("xfce4-terminal")

    if not _HAVE_REQUESTS:
        packages.append("python3-requests")

    if not _HAVE_VDF:
        packages.append("python3-vdf")

    if packages:
        if not ran_update:
            ex("apt", "update", "-y")
        print(f"Installing: {', '.join(packages)}")
        ex("apt", "install", "-y", *packages)

    # Installing the steam .deb will add valve repositories which we
    # need to fetch the metadata for here. Then, we need to install the
    # last library package we need from that repository to allow steam
    # to run properly.
    ex("apt", "update", "-y")
    ex("apt", "install", "-y", "steam-libs-amd64:amd64")


def keyd_setup(config):
    # Point the keyd default config to the active keymap symlink.
    # We do this so we have permission to change the active conf without root!
    # (default: /etc/keyd/default.conf => ~/RetroPie/steam/keymaps/active.conf)
    mklink(config.keyd_config, config.active_keymap)

    # Point the active keymap file in turn to our user-owned default keymap
    # (default: ~/RetroPie/steam/keymaps/active.conf =>
    #                   ~/RetroPie/steam/keymaps/default.conf)
    mklink(config.active_keymap, config.default_keymap)
    uid = getpwnam(config.user)[2]
    os.chown(config.active_keymap, uid, uid, follow_symlinks=False)

    if not os.path.exists(config.default_keymap):
        with open(config.default_keymap, "w") as outfile:
            outfile.write("# This space for rent!\n")
        shutil.chown(config.default_keymap, user=config.user, group=config.user)

    with open("/etc/keyd/common", "w") as outfile:
        outfile.write("[ids]\n\n")
        outfile.write("d208:0310:bc611fc2\n\n")
        outfile.write("[aliases]\n\n")

        for alias, value in keycfg.keycfg.items():
            outfile.write(f"{value} = {alias}\n")

        outfile.write("\n")
        outfile.write("[main]\n\n")
        outfile.write("p1_a = command(pkill -f -15 vent)\n")

    # Add the kiosk user to the 'keyd' group for rootless access to 'keyd reload'
    ex("systemctl", "enable", "keyd")
    ex("usermod", "-aG", "keyd", config.user)


def first_run_setup(config):
    ex("systemctl", "restart", "systemd-timesyncd")
    external_tool_setup()

    for p in (
            config.steam_dir,
            config.keymap_dir,
            config.game_dir,
            config.autostart_config.parent
    ):
        os.makedirs(p, exist_ok=True)
        shutil.chown(p, user=config.user, group=config.user)

    keyd_setup(config)
    add_steam_system(config.es_config, config.game_dir)

    # Prime steamcmd and fetch updates from valve, etc.
    ex("su", "-c", "steamcmd +exit", "-", config.user)

    # Prime the steam client itself
    # FIXME: This is broken, steam segfaults when launched this way...
    # proc = subprocess.Popen(["su", "-c", "steam", "-", config.user])
    # ex("su", "-c", "steam -shutdown", "-", config.user)
    # proc.wait()

    # Modify the autostart entry for RetroPie to launch the "kiosk"
    # launcher which will in turn launch steam and emulationstation
    # both.
    cfg = ConfigParser()
    if config.autostart_config.exists():
        cfg.read(config.autostart_config)
        cfg['Desktop Entry']['Exec'] = 'kiosk-launcher'
    else:
        cfg['Desktop Entry'] = {
            'Type': 'Application',
            'Exec': 'kiosk-launcher',
            'Hidden': 'false',
            'NoDisplay': 'false',
            'X-GNOME-Autostart-enabled': 'true',
            'Name[de_DE]': 'RetroPie',
            'Name': 'rpie',
            'Comment[de_DE]': 'RetroPie',
            'Comment': 'retropie',
            'Icon': '/usr/local/share/icons/retropie.svg',
            'Categories': 'Game',
        }

    with open(config.autostart_config, "w") as outfile:
        cfg.write(outfile)
    shutil.chown(config.autostart_config, user=config.user, group=config.user)

    # install vent (launcher), kiosk, kiosk-launcher, vent (installer) scripts


def do_main():
    cfg = get_configuration()
    print(cfg)
    first_run_setup(cfg)


def main():
    main_wrapper(do_main)


if __name__ == '__main__':
    main()
