#!/bin/env python

import json
import requests
import sys
import datetime
from subprocess import call, check_output
import logging
import os
# from multiprocessing import Process
logging.basicConfig(
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

# ORGANIZATION = "legleux"
# REPOSITORY = "scheduled"
# BRANCH = "main"
SOURCE_ORG = "legleux"
SOURCE_REPO = "am_test"
SOURCE_BRANCH = "main"

RELEASES_ORG = "legleux"
RELEASES_REPO = "scheduled"
RELEASES_URL = f"https://api.github.com/repos/{RELEASES_ORG}/{RELEASES_REPO}"

ASSETS_URL = f"{RELEASES_URL}/releases/latest"

SOURCE_REPO = f"https://api.github.com/repos/{SOURCE_ORG}/{SOURCE_REPO}/commits/{SOURCE_BRANCH}"

RIPPLED_INSTALL_PATH = "/opt/rippled/bin"


def get_latest_source_commit():
    latest_commit = json.loads(requests.get(SOURCE_REPO).content).get('sha')[0:9]
    return latest_commit


def get_installed_version():
    version_raw = check_output(['/opt/rippled/bin/rippled', '--version'])
    version_str = version_raw.decode().replace('\n', '')
    version_short = version_str.split("+")[1][0:9]
    return version_short


def get_release_url():
    assets = json.loads(requests.get(ASSETS_URL).content)
    latest_asset = assets.get('assets')[-1]
    return latest_asset.get("browser_download_url")


def get_latest_release_version():
    try:
        assets = json.loads(requests.get(ASSETS_URL).content)
        version = assets.get('name').split(" ")[1]
    except Exception as e:
        logging.info(e)
    return version


def release_needed():
    return get_latest_source_commit() != get_latest_release_version()


def dl_latest():
    release_url = get_release_url()
    binary = requests.get(release_url)
    assets = json.loads(requests.get(ASSETS_URL).content)
    latest_asset = assets.get('assets')[-1]
    name = latest_asset.get("name")
    rippled_path = RIPPLED_INSTALL_PATH + name
    version = assets.get('name').split(" ")[1]
    open(rippled_path, "wb").write(binary.content)
    check_output(['chmod', '+x', rippled_path])
    logging.info(f"Downloaded: {name} {version}")


# def install_latest():
#     call(['rm', '/opt/rippled/rippled'])
#     os.chdir('/tmp')
#     dl_latest()
#     call(['mv', 'rippled', '/opt/rippled/rippled'])


def start_rippled():
    pass


if __name__ == "__main__":

    command = sys.argv.pop()

    if command == 'check_release_needed':
        if release_needed():
            # update()
            logging.info("Need to build release")
            print("true")
        else:
            logging.info("Up to date")
    if command == 'check_latest':
        try:
            version = get_installed_version()
            if version != get_latest_release_version():
                dl_latest()
        except Exception as e:
            logging.warning(e)
