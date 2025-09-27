#!/usr/bin/env python3

import argparse
import datetime
import json
import logging
import os
from pathlib import Path
import stat
import subprocess
from xml.etree import ElementTree

import requests

from .common import get_configuration, main_wrapper
from . import keycfg
from .valve import (
    get_executable,
    load_or_fetch_info,
)


LOG = logging.getLogger('vent')


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
            pass
            #print(f"skipping {url}, already in queue")
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
                        return (
                            'https://video.akamai.steamstatic.com/'
                            'store_trailers/' + fmt['filename']
                        )
        return None

    trailer = _find_trailer()
    if trailer:
        _enqueue(trailer, None, 'trailer')

    for local_name, url in queue.items():
        cache_asset(cachedir, appID, url, local_name)


def write_keymap(path, appID, info):
    print(f"writing keymap to {path}")
    name = info['vdf']['common']['name']

    with open(path, "w") as outfile:
        outfile.write(f"# Configuration for {name}\n")
        outfile.write(f"# Steam appID: {appID}\n\n")
        outfile.write("include common\n\n")
        outfile.write("[main]\n\n")
        for alias, value in keycfg.keycfg.items():
            outfile.write(f"{alias} = {value}\n")
        outfile.write("\n")


def write_runscript(path, appID):
    print(f"writing runscript to {path}")
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
    # metadata['thumbnail'] = '...'

    video_path = os.path.join(local_dir, 'trailer.mp4')
    if os.path.exists(video_path):
        print(f"using trailer '{video_path}'")
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

    metadata['path'] = str(script_path)

    return metadata


def update_gamelist_xml(game_entry):
    gamelist_path = os.path.expanduser(
        "~/.emulationstation/gamelists/steam/gamelist.xml"
    )
    os.makedirs(Path(gamelist_path).parent, exist_ok=True)

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
            print(f"Updating gamelist.xml entry in '{gamelist_path}'")
            game = elem
            new_element = False
            break

    if game is None:
        print(f"Adding gamelist.xml entry to '{gamelist_path}'")
        game = ElementTree.Element("game")
        for key, value in game_entry.items():
            node = ElementTree.Element(key)
            node.text = value
            game.append(node)
        root.append(game)

    ElementTree.indent(tree)
    #print(ElementTree.tostring(root, encoding='UTF-8').decode())
    tree.write(gamelist_path, encoding='UTF-8')


def install_game(cfg, appID):
    os.makedirs(cfg.cache_dir, exist_ok=True)

    print("")
    print("Fetching metadata ...")
    info = load_or_fetch_info(appID, cfg.cache_dir)
    print("")

    # Just to ensure that we can actually identify the binary when it
    # comes time to launch the game.
    name = info['vdf']['common']['name']
    exec_name = get_executable(info)

    print(f"Steam appID: {appID}")
    print(f"Steam game: {name}")
    print(f"Steam game executable: {exec_name}")
    print("")

    print("Fetching assets ...")
    get_images(appID, info, cfg.cache_dir)
    print("")

    subprocess.run([
        "steamcmd",
        "+login", "LowellMakes",
        "+app_update", str(appID),
        "+exit",
    ], check=True)

    # Guess which image to use for our thumbnail. Go through the list
    # until we find one that seems suitable.
    for img_name in (
        'hero_capsule_2x.jpg',
        'library_capsule_2x.jpg',
        'hero_capsule.jpg',
        'library_capsule.jpg',
        'main_capsule.jpg',
        'header.jpg',
        'small_capsule.jpg'
    ):
        libimg = os.path.join(cfg.cache_dir, str(appID), img_name)
        if os.path.exists(libimg):
            break
    else:
        libimg = None

    print(f"using thumbnail {libimg}")
    script_path = cfg.game_dir.joinpath(f"{name}.sh")
    write_runscript(script_path, appID)

    keymap_path = cfg.keymap_dir.joinpath(f"{appID}.conf")
    write_keymap(keymap_path, appID, info)

    game_entry = generate_gamelist_entry(info, appID, libimg, script_path, cfg.cache_dir)
    update_gamelist_xml(game_entry)

    print("All done!")
    print("Remember to edit the key configuration file to finish installation:")
    print(f"    {str(keymap_path)}")


def do_main():
    parser = argparse.ArgumentParser()
    parser.add_argument("appID")
    args = parser.parse_args()

    cfg = get_configuration()
    for key, value in cfg.__dict__.items():
        print(f"{key:20s} {value}")

    install_game(cfg, args.appID)


def main():
    main_wrapper(do_main)


if __name__ == '__main__':
    main()
