import dataclasses
import json
import logging
import os
import urllib

import requests
import vdf

from common import ex


LOG = logging.getLogger('vent')


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


def get_info(appID):
    ret = ex(
        "steamcmd",
        "+app_info_print",
        str(appID),
        "+exit",
        capture_output=True
    )
    output = ret.stdout.decode()

    index = output.find(f'"{appID}"')
    if index == -1:
        LOG.error("Could not parse steamcmd output, start of VDF metadata could not be found")
        LOG.debug(output)
        raise Exception("Could not identify the start of VDF metadata")

    output = output[index:]
    index = output.find("Unloading Steam API")
    if index != -1:
        output = output[:index]
    info = vdf.loads(output)

    return info[str(appID)]


def get_web_info(appID):
    input_json = {
        "ids": [{"appid": appID}],
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
