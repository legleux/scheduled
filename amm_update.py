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

RIPPLED_INSTALL_PATH = "/opt/rippled/bin/"


def get_latest_source_commit():
    latest_commit = json.loads(requests.get(SOURCE_REPO).content).get('sha')[0:7]
    return latest_commit


def get_installed_version():
    try:
        version_raw = check_output(['/opt/rippled/bin/rippled', '--version'])
        version_str = version_raw.decode().replace('\n', '')
        version_short = version_str.split("+")[1][0:7]
        return version_short
    except Exception as e:
        logging.info('no rippled installed')
        return None


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
    bin_name = 'rippled'
    release_url = get_release_url()
    logging.info(f"Release at URL: {release_url}")
    logging.info(f"Downloading release...")

    binary = requests.get(release_url)
    assets = json.loads(requests.get(ASSETS_URL).content)
    latest_asset = assets.get('assets')[-1]
    name = latest_asset.get("name")
    rippled_path = RIPPLED_INSTALL_PATH + bin_name

    logging.info(f"Installing to: {rippled_path}")
    version = assets.get('name').split(" ")[1]
    tar_path = f'/tmp/rippled-{version}/'
    call(['rm', '-rf', tar_path])
    os.mkdir(tar_path)
    tar_file = f'{tar_path}{name}'
    open(tar_file, "wb").write(binary.content)

    call(['rm', '-rf', RIPPLED_INSTALL_PATH, '|| true'])
    os.mkdir(RIPPLED_INSTALL_PATH)
    check_output(['tar', 'xzvf', tar_file, '-C', RIPPLED_INSTALL_PATH])
    logging.info(f"Chmoding to: {rippled_path}")
    check_output(['chmod', '+x', rippled_path])
    logging.info(f"Installed: {name} {version}")
    with open('/opt/rippled/bin/gitrev.txt', 'w') as f:
        f.write(version)
    ripd_ver = check_output([rippled_path, '--version']).decode()
    logging.info(f"Rippled thinks it's {ripd_ver}")


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
            latest_release = get_latest_release_version()
            version = get_installed_version()
            if version != latest_release:
                logging.info(f'local version mismatch {version} not {latest_release}')
                if latest_release != check_output(['cat', '/opt/rippled/bin/gitrev.txt']).decode():
                    logging.info('gitrev.txt mismatch, must really be outdated...')
                    dl_latest()
            else:
                logging.info(f'Local install {version} matches latest release {latest_release}')
        except Exception as e:
            logging.warning(e)
