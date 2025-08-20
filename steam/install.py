#!/usr/bin/env python3

import dataclasses
import datetime
import json
import logging
from logging.handlers import SysLogHandler
import os
from pathlib import Path
import select
import signal
import subprocess
import stat
import sys
import time
import urllib
from xml.etree import ElementTree

import requests
import vdf


@dataclasses.dataclass
class URL:
    """
    Mutable version of urllib's ParseResult.

    :param url_str: URL to parse into components.
    """
    scheme: str
    netloc: str
    path: str
    params: str
    query: str
    fragment: str

    def __init__(self, url_str: str = ''):
        self._parsed = urllib.parse.urlparse(url_str)
        self.scheme = self._parsed.scheme
        self.netloc = self._parsed.netloc
        self.path = self._parsed.path
        self.params = self._parsed.params
        self.query = self._parsed.query
        self.fragment = self._parsed.fragment

    def build(self) -> str:
        """
        Re-build the current components back into a URL.
        """
        values = [str(v) for v in dataclasses.asdict(self).values()]
        return urllib.parse.urlunparse(values)

    def __str__(self) -> str:
        return self.build()


# Your Steam Web API Key
# Key: BA511D8B6FFE854B02DF6C9B8A401850
# Domain Name: lowellmakes.com


LOG = logging.getLogger('vent')


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
    'p1_select':  '5',
    'p1_start': '1',

    'p2_up': 'r',
    'p2_down': 'f',
    'p2_left': 'd',
    'p2_right': 'g',
    'p2_1': 'a',
    'p2_2': 's',
    'p2_3': 'q',
    'p2_4': 'w',
    'p2_5': 'i',
    'p2_6': 'k',
    'p2_7': 'j',
    'p2_8': 'l',
    'p2_a': 'tab',
    'p2_b': 'esc',
    'p2_select': '6',
    'p2_start': '2',
}


def get_info(appID):
    ret = subprocess.run(
        ["steamcmd", "+app_info_print", str(appID), "+exit"],
        capture_output=True,
        check=True
    )

    output = ret.stdout.decode()

    index = output.find(f'"{appID}"')
    if index == -1:
        raise Exception("Could not identify the start of VDF metadata")

    output = output[index:]
    index = output.find("Unloading Steam API")
    if index != -1:
        output = output[:index]
    info = vdf.loads(output)

    return info[str(appID)]


def get_web_info(appID):
    input_json = {
        "ids": [{ "appid": appID }],
        "context": {
            "language": "english",
            "elanguage": 0,
            "country_code": "US",
            "steam_realm": 0
        },
        "data_request": {
            "include_assets": True,
            "include_release": True,
            "include_platforms": True,
            "include_all_purchase_options": True,
            "include_screenshots": True,
            "include_trailers": True,
            "include_ratings": True,
            "include_reviews": True,
            "include_basic_info": True,
            "include_supported_languages": True,
            "include_full_description": True,
            "include_included_items": True,
            "include_assets_without_overrides": True,
            "include_links": True
        }
    }

    base_uri = "https://api.steampowered.com/IStoreBrowseService/GetItems/v1/"

    url = URL(base_uri)
    url.query = urllib.parse.urlencode({
        "input_json": json.dumps(input_json),
    })

    rsp = requests.get(url)
    assert rsp.status_code == 200

    print(url)
    data = rsp.json()
    return data['response']['store_items'][0]


def get_store_info(appID):
    base_uri = "https://store.steampowered.com/api/appdetails"
    # "?appids=1921550"

    url = URL(base_uri)
    url.query = urllib.parse.urlencode({
        "appids": str(appID),
    })

    rsp = requests.get(url)
    assert rsp.status_code == 200

    print(url)
    data = rsp.json()
    return data[str(appID)]['data']


def cache_asset(cachedir, appID, url, local_name):
    local_dir = os.path.join(cachedir, appID + '/')
    os.makedirs(local_dir, exist_ok=True)

    local_path = os.path.join(local_dir, local_name)
    if not os.path.exists(local_path):
        rsp = requests.get(url)
        print(f"{rsp.status_code}: {url}")
        if rsp.status_code == 200:
            with open(local_path, "wb") as outfile:
                outfile.write(rsp.content)


def get_images(appID, info, cachedir):
    # https://partner.steamgames.com/doc/store/assets
    # https://myopic.design/tools/steam-asset-scraper/?appid=1420810

    store_url_base = f'https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{appID}/'
    community_url = f"https://cdn.fastly.steamstatic.com/steamcommunity/public/images/apps/{appID}/"

    queue = {}

    def _enqueue(url, lang, basename):
        ext = Path(url).suffix[1:]
        key = f"{basename}.{ext}"

        if url in queue.values():
            print(f"skipping {url}, already in queue")
        elif key in queue:
            queue[f"{basename}-{lang}.{ext}"] = url
        else:
            queue[key] = url


    assets = info['web']['assets']
    for key, value in assets.items():
        if key == 'asset_url_format':
            continue

        if key == 'page_background_path':
            pass  # TODO
        elif key == 'community_icon':
            _enqueue(community_url + f"{value}.jpg", None, "community_icon")
        else:
            _enqueue(store_url_base + value, None, key)


    # URLs harvested from app_info_print

    for lang, value in info['vdf']['common'].get('small_capsule', {}).items():
        _enqueue(store_url_base + value, lang, "small_capsule")

    for lang, value in info['vdf']['common'].get('header_image', {}).items():
        _enqueue(store_url_base + value, lang, "header_image")

    assets = info['vdf']['common'].get('library_assets_full', {})
    for name, obj in assets.items():
        # names are e.g. (library_capsule, library_hero, library_logo)
        for key, value in obj.items():
            if key == 'logo_position':
                continue
            if key not in ('image', 'image2x'):
                print(f"Warn: unrecognized asset key '{key}'")
                continue
            for lang, fname in value.items():
                static_name = name
                if key == 'image2x':
                    static_name += '_2x'
                _enqueue(store_url_base + fname, lang, static_name)

    # Misc assets
    def _misc_enqueue(name, ext):
        if name in info['vdf']['common']:
            _enqueue(community_url + info['vdf']['common'][name] + f".{ext}", None, name)

    _misc_enqueue('clienttga', 'tga')
    _misc_enqueue('clienticon', 'ico')
    _misc_enqueue('icon', 'jpg')
    _misc_enqueue('logo', 'jpg')
    _misc_enqueue('logo_small', 'jpg')
    _misc_enqueue('clienticns', 'icns')
    _misc_enqueue('linuxclienticon', 'zip')

    # This asset isn't in any metadata I can see, just guess it.
    _enqueue(store_url_base + "page_bg_raw.jpg", None, "page_bg_raw")

    def _find_trailer():
        for trailer in info['web']['trailers'].get('highlights', []):
            if 'trailer_max' in trailer:
                for fmt in trailer['trailer_max']:
                    if fmt['type'] == 'video/mp4':
                        return 'https://video.akamai.steamstatic.com/store_trailers/' + fmt['filename']
        return None

    trailer = _find_trailer()
    if trailer:
        _enqueue(trailer, None, 'trailer')

    for local_name, url in queue.items():
        cache_asset(cachedir, appID, url, local_name)

    print(json.dumps(queue, indent=2))
    print("")


def get_executable(info):
    launch = info['vdf']['config']['launch']

    for execinfo in launch.values():
        if execinfo.get('config', {}).get('oslist', '') == 'linux':
            executable = execinfo['executable']
            if executable.startswith("./"):
                executable = executable[2:]
            return executable

    for execinfo in launch.values():
        if execinfo.get('config', {}).get('oslist', None) in ('windows', None):
            return execinfo['executable']

    raise Exception("Couldn't find a suitable executable to run this game ...?")


def load_or_fetch_info(appID, cachedir):
    local_dir = os.path.join(cachedir, str(appID))
    os.makedirs(local_dir, exist_ok=True)

    def _cache_fetch(target, retrieve_fn):
        if os.path.exists(target):
            with open(target, "r") as infile:
                data = json.load(infile)
        else:
            data = retrieve_fn()
            with open(target, "w") as outfile:
                json.dump(data, outfile, indent=2)
        return data


    # steamcmd app_info_print {appID}
    vdf_info = _cache_fetch(
        os.path.join(local_dir, "vdf.json"),
        lambda: get_info(appID),
    )

    # https://api.steampowered.com/IStoreBrowseService/GetItems/v1/? ...
    web_info = _cache_fetch(
        os.path.join(local_dir, "web.json"),
        lambda: get_web_info(appID),
    )

    # https://store.steampowered.com/api/appdetails?appids=...
    store_info = _cache_fetch(
        os.path.join(local_dir, "store.json"),
        lambda: get_store_info(appID),
    )

    info = {
        'vdf': vdf_info,
        'web': web_info,
        'store': store_info,
    }
    return info


def xfconf_query(channel, prop, value=None):
    if value:
        subprocess.run([
            "xfconf-query",
            "--create",
            "--type", "string",
            "-c", channel,
            "-p", prop,
            "-s", value,
        ])
    else:
        subprocess.run([
            "xfconf-query",
            "-c", channel,
            "-p", prop,
            "-r",
        ])


def remove_splash():
    xfconf_query("xfce4-terminal", "/background-image-file")
    xfconf_query("xfce4-terminal", "/background-mode")
    xfconf_query("xfce4-terminal", "/background-image-style")


def do_configure_splash(img):
    xfconf_query("xfce4-terminal", "/font-name", "Monospace Bold 20")
    if img:
        xfconf_query("xfce4-terminal", "/background-image-file", img)
        xfconf_query("xfce4-terminal", "/background-mode", "TERMINAL_BACKGROUND_IMAGE")
        xfconf_query("xfce4-terminal", "/background-image-style", "TERMINAL_BACKGROUND_STYLE_SCALED")
    else:
        remove_splash()


def configure_splash(img):
    try:
        do_configure_splash(img)
    except FileNotFoundError:
        print("Warning: Could not change terminal background. Is xfconf-query installed?")


def write_keymap(path, appID, info):
    name = info['vdf']['common']['name']

    with open(path, "w") as outfile:
        outfile.write(f"# Configuration for {name}\n")
        outfile.write(f"# Steam appID: {appID}\n\n")
        outfile.write("include common\n\n")
        outfile.write("[main]\n\n")
        for alias, value in keycfg.items():
            outfile.write(f"{alias} = {value}\n")
        outfile.write("\n")


def write_runscript(path, appID):
    os.makedirs(Path(path).parent, exist_ok=True)

    with open(path, 'w', encoding='UTF-8') as outfile:
        outfile.write("#!/usr/bin/env bash\n")
        outfile.write(f"vent {appID}\n")

    perms = os.stat(path).st_mode
    os.chmod(path, perms | stat.S_IXUSR) 


def generate_gamelist_entry(info, appID, libimg, script_path, cachedir):
    local_dir = os.path.join(cachedir, str(appID))

    metadata = {}

    metadata['name'] = info['vdf']['common']['name']
    metadata['steam_appID'] = appID
    metadata['desc'] = info['web']['basic_info']['short_description']
    metadata['image'] = libimg
    #metadata['thumbnail'] = '...'

    video_path = os.path.join(local_dir, 'trailer.mp4')
    if os.path.exists(video_path):
        metadata['video'] = video_path

    if 'review_percentage' in info['vdf']['common']:
        metadata['rating'] = str(int(info['vdf']['common']['review_percentage']) / 100.0)

    ts = None
    if info['vdf']['common'].get('original_release_date'):
        ts = info['vdf']['common']['original_release_date']
    elif info['vdf']['common'].get('steam_release_date'):
        ts = info['vdf']['common']['steam_release_date']
    if ts:
        dt = datetime.datetime.fromtimestamp(int(ts))
        metadata['releasedate'] = dt.strftime("%Y%m%dT%H%M%S")

    metadata['developer'] = info['vdf'].get('extended', {}).get('developer', '')
    metadata['publisher'] = info['vdf'].get('extended', {}).get('publisher', '')

    if 'genres' in info['store']:
        metadata['genre'] = info['store']['genres'][0]['description']

    for cat in info['store'].get('categories', []):
        if cat['description'] == 'Single-player':
            metadata['players'] = "1"
            break

    metadata['path'] = script_path

    return metadata


def update_gamelist_xml(game_entry):
    gamelist_path = os.path.expanduser("~/.emulationstation/gamelists/steam/gamelist.xml")

    try:
        tree = ElementTree.parse(gamelist_path)
        root = tree.getroot()
    except FileNotFoundError:
        root = ElementTree.Element("gameList")
        tree = ElementTree.ElementTree(root)

    game = None
    new_element = True

    for elem in root.iter(tag='game'):
        path = elem.find('path')
        if path is not None and path.text == game_entry['path']:
            print("Existing entry found, updating/overwriting")
            game = elem
            new_element = False
            break
    
    if game is None:
        print("No existing game entry found, creating new")
        game = ElementTree.Element("game")
        for key, value in game_entry.items():
            node = ElementTree.Element(key)
            node.text = value
            game.append(node)
        root.append(game)

    ElementTree.indent(tree)
    print(ElementTree.tostring(root, encoding='UTF-8').decode())
    tree.write(gamelist_path, encoding='UTF-8')


def install_game(appID, rootdir):
    cachedir = os.path.join(rootdir, "cache/")
    os.makedirs(cachedir, exist_ok=True)

    info = load_or_fetch_info(appID, cachedir)
    get_images(appID, info, cachedir)

    # Just to ensure that we can actually identify the binary when it
    # comes time to launch the game.
    get_executable(info)

    # Guess which image to use for our library entry
    for name in (
        'hero_capsule_2x.jpg',
        'library_capsule_2x.jpg',
        'hero_capsule.jpg',
        'library_capsule.jpg',
        'main_capsule.jpg',
        'header.jpg',
        'small_capsule.jpg'
    ):
        libimg = os.path.join(cachedir, str(appID), name)
        if os.path.exists(libimg):
            break
    else:
        libimg = None
    configure_splash(libimg)

    name = info['vdf']['common']['name']
    script_path = f'/home/nago/RetroPie/steam/menu/{name}.sh'

    write_runscript(script_path, appID)
    write_keymap(f"/home/nago/RetroPie/steam/keymaps/{appID}.conf", appID, info)

    game_entry = generate_gamelist_entry(info, appID, libimg, script_path, cachedir)
    update_gamelist_xml(game_entry)

    #print("Looking pretty")
    #for i in range(10):
    #    time.sleep(1)


def do_launch(active_link, keymap, appID, steam_root, default_map):
    try:
        install_game(appID, str(steam_root))
    finally:
        remove_splash()


def do_main():
    # /etc/keyd/default.conf is a symlink to {active_link}.
    # {rootdir}/keymaps/default.conf exists and is a suitable keymap when no steam game is running.
    # {rootdir}/keymaps/{appID}.conf, if it exists, should be a suitable keymap config for that game.

    user = os.environ.get("SUDO_USER")
    if not user:
        user = os.environ.get("USER")
    if not user:
        # todo: could use 'whoami' ...
        raise Exception("Failed to determine who is running this script. Who are you?")

    appID = sys.argv[1]

    home = Path(os.path.expanduser(f"~{user}"))
    rp_root = home.joinpath("RetroPie")
    steam_root = rp_root.joinpath("steam")
    keymap_dir = steam_root.joinpath("keymaps")
    active_link = keymap_dir.joinpath("active.conf")
    default_map = keymap_dir.joinpath("default.conf")
    keymap = keymap_dir.joinpath(f"{appID}.conf")

    os.makedirs(keymap_dir, exist_ok=True)

    LOG.debug("do_main() ...")
    LOG.debug("  steam_root=%s", steam_root)
    LOG.debug("  keymap=%s", keymap)
    LOG.debug("  active_link=%s", active_link)
    LOG.debug("  default_map=%s", default_map)
    LOG.debug("  appID=%s", appID)

    do_launch(active_link, keymap, appID, steam_root, default_map)


def configure_logging():
    service_name = 'vent'
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
        logging.Formatter(f"{service_name}: %(name)s: %(message)s")
    )

    LOG.setLevel(logging.DEBUG)
    LOG.addHandler(syslog)


def main():
    configure_logging()

    try:
        do_main()
    except:
        LOG.exception("Something broke!")
        raise


if __name__ == '__main__':
    main()
