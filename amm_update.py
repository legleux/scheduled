#!/bin/env python

import json
import requests
import sys
import datetime
from subprocess import call
import logging
import os
# from multiprocessing import Process
logging.basicConfig(
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

ORGANIZATION = "legleux"
ORGANIZATION = "gregtcam"
REPOSITORY = "scheduled"
REPOSITORY = "rippled"
BRANCH = "main"
BRANCH = "amm-core-functionality"
BASE_URL = f"https://api.github.com/repos/{ORGANIZATION}/{REPOSITORY}"
ASSETS_URL = f"{BASE_URL}/releases/latest"


def get_latest_source_commit():
    SOURCE_REPO = "https://api.github.com/repos/legleux/source/commits/master"
    latest_commit = json.loads(requests.get(SOURCE_REPO).content).get('sha')[0:7]
    return latest_commit


def get_installed_version():
    version = call(["cat", "/opt/rippled/version.txt"])
    return version


def get_release_url():
    assets = json.loads(requests.get(ASSETS_URL).content)
    latest_asset = assets.get('assets')[-1]
    return latest_asset.get("browser_download_url")


def get_latest_release_version():
    assets = json.loads(requests.get(ASSETS_URL).content)
    version = assets.get('name').split(" ")[1]
    return version


def release_needed():
    return get_latest_source_commit() != get_latest_release_version()


def dl_latest():
    release_url = get_release_url()
    binary = requests.get(release_url)
    assets = json.loads(requests.get(ASSETS_URL).content)
    latest_asset = assets.get('assets')[-1]
    name = latest_asset.get("name")
    version = assets.get('name').split(" ")[1]
    open(name, "wb").write(binary.content)
    logging.info(f"Downloaded: {name} {version}")


def install_latest():
    call(['rm', '/opt/rippled/rippled'])
    os.chdir('/tmp')
    dl_latest()
    call(['mv', 'rippled', '/opt/rippled/rippled'])


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
            version = call(['/opt/rippled/bin/rippled', '--version'])
            version = version.split("+")[1]
            if version != get_latest_release_version():
                install_latest()
        except Exception as e:
            logging.warning(e)


    # elif command == 'return_true':
    #     print("true")
    # elif command == 'return_false':
    #     print("false")
    # if get_installed_version() !=  get_latest_release():
    #     print("need to update local")

    # if command == "test":
    #     now = datetime.datetime.now()
    #     print(f"Checking @ {now}...")
    #     with open("/opt/runme/testfile.txt", "a") as f:
    #         f.write("#!/bin/bash\n")
    #         f.write("some data\n")
    #         f.write(f'{now}\n"')
    # elif command == "check":
    #     print("gonna check")
    # else:
    #     print("gonna update")
