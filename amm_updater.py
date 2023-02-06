#!/bin/env python

import json
import requests
import sys
import datetime
from subprocess import call, check_output
import subprocess
import logging
import os
import argparse
import shutil

filename='amm_updater.log'
# logger = logging.getLogger("amm_updater")
# fh = logging.FileHandler(filename, mode='a', encoding=None, delay=False, errors=None)
logging.basicConfig(
                    # handlers=[fh],
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
# logger.addHandler(fh)

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("paramiko").setLevel(logging.WARNING)
""" TODO:
don't download if already did
clean up tmp dir
"""
SOURCE_ORG = "gregtatcam"
SOURCE_REPO = "rippled"
SOURCE_BRANCH = "amm-core-functionality"

RELEASES_ORG = "legleux"
RELEASES_REPO = "scheduled"
RELEASES_URL = f"https://api.github.com/repos/{RELEASES_ORG}/{RELEASES_REPO}"

ASSETS_URL = f"{RELEASES_URL}/releases/latest"

SOURCE_REPO = f"https://api.github.com/repos/{SOURCE_ORG}/{SOURCE_REPO}/commits/{SOURCE_BRANCH}"

RIPPLED_INSTALL_PATH = "/opt/ripple/bin/"
GITREV_FILE = f'{RIPPLED_INSTALL_PATH}gitrev.txt'
TMP_DIR = "/tmp"

AMM_DB_PATH = '/space/rippled/db/'
AMM_LOG_PATH =  '/space/rippled/log/debug.log'
DB_PATH = '/var/lib/rippled/db/'
LOG_PATH =  '/var/log/rippled/debug.log'

def get_latest_source_commit():
    response = requests.get(SOURCE_REPO)
    response_content = response.content
    if response.ok:
        limit = response.headers['X-RateLimit-Limit']
        used = response.headers['X-RateLimit-Used']
        logging.debug(f"{used}/{limit} API calls used")

        latest_commit = response.json().get('sha')[0:7]
        return latest_commit
    else:
        logging.info(f"Couldnt get latest commit from {SOURCE_REPO}")
        logging.debug(f"Returned: {response.status_code}")
        logging.debug(response.json()['message'])
        t = response.headers['X-RateLimit-Reset']
        tt = datetime.datetime.fromtimestamp(int(t)).strftime('%Y-%m-%d %H:%M:%S')
        logging.debug(f"Rate limited until: {tt}")
        sys.exit()


def get_installed_version():
    try:
        version_raw = check_output([RIPPLED_INSTALL_PATH + 'rippled', '--version'])
        version_str = version_raw.decode().replace('\n', '')
        version_short = version_str.split("+")[1][0:7]
        return version_short
    except Exception as e:
        logging.info(e)
        logging.info('no rippled installed')
        logging.info('debug not installed')
    finally:
        dl_latest()


def get_release_url():
    assets = json.loads(requests.get(ASSETS_URL).content)
    latest_asset = assets.get('assets')[-1]
    return latest_asset.get("browser_download_url")


def get_latest_release_version():
    # try:
    assets = json.loads(requests.get(ASSETS_URL).content)
    version = assets.get('name').split(" ")[1][0:7]
    return version
    # except Exception as e:
    #     logging.info(e)


def write_gitrev_file():
    version = get_latest_release_version()
    logging.info(f'Wrote {version} to {GITREV_FILE}')

    with open(GITREV_FILE, 'w') as f:
        f.write(version)
    logging.info(f'Wrote {version} to {GITREV_FILE}')


def release_needed():
    src_hash = get_latest_source_commit()
    bin_hash = get_latest_release_version()
    logging.debug(f"Source code: {src_hash}] Latest binary built: {bin_hash}")
    rel_needed = src_hash != bin_hash
    return rel_needed


def get_rippled_version():
    output = subprocess.check_output("rippled --version".split(" "))
    version = output.decode().rstrip().split(" ")[2].split("+")[1][:8]
    return version


def install_latest():
    logging.info("Installing latest rippled.")
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
    tar_path = f'/{TMP_DIR}/rippled-{version}/'
    call(['rm', '-rf', tar_path])
    os.mkdir(tar_path)
    tar_file = f'{tar_path}{name}'
    open(tar_file, "wb").write(binary.content)

    call(['rm', '-rf', RIPPLED_INSTALL_PATH, '|| true'])
    os.mkdir(RIPPLED_INSTALL_PATH)
    try:
        check_output(['tar', 'xzvf', tar_file, '-C', RIPPLED_INSTALL_PATH])
    except Exception as e:
        logging.info(f"Couldn't untar {tar_file}")
    logging.info(f"Chmoding to: {rippled_path}")
    check_output(['chmod', '+x', rippled_path])
    logging.info(f"Installed: {name} {version}")
    write_gitrev_file()
    ripd_ver = check_output([rippled_path, '--version']).decode()
    logging.info(f"Rippled thinks it's {ripd_ver}")
    call(['rm', '-rf', tar_path])


def restart_rippled():
    output = subprocess.call("sudo systemctl restart rippled".split(" "))
    return output


def stop_rippled():
    o = subprocess.run("sudo systemctl stop rippled".split(" "))
    return o


def remove(path):
    #if path exists
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    else:
        raise ValueError(f"Couldn't delete {path}")


def delete_db():
    paths = [ path for path in [DB_PATH, LOG_PATH]]
    for path in paths:
        logging.info(f"Removing {path}")
        remove(path)


def update_rippled(reset_network=False, restart=True):
    install_latest()
    if reset_network:
        logging.info("Stopping rippled")
        stop_rippled()
        logging.info("Deleting db")
        delete_db()
    logging.info("Starting rippled")
    if restart: # may want to manually start rippled with --start flag t
        restart_rippled()
    ## confirm up and running


def remote_start(reset=False):

    command = 'update_and_reset_network' if reset else 'update_rippled'
    for server in ['val6', "jammy", "focal"]:
        logging.info(f"Logging in to {server} to {command}")
        o = subprocess.run(f"ssh {server} sudo systemctl start amm_updater@--{command}".split(" "))
        logging.info(o.stdout)


def install_updater(server):

    scp = subprocess.run(f"scp amm_updater.py {server}:~".split(" "))
    # mkdir if not existing
    mv = subprocess.run(f"ssh {server} sudo  mv ~/amm_updater.py /opt/amm_updater/amm_updater.py".split(" "))
    # mv = subprocess.run(f"ssh {server} sudo mkdir /opt/amm_updater && sudo  mv ~/amm_updater.py /opt/amm_updater/amm_updater.py".split(" "))
    serv = subprocess.run(f"scp amm_updater.service {server}:~".split(" "))
    mvserv = subprocess.run(f"ssh {server} sudo  mv ~/amm_updater.service /etc/systemd/system/amm_updater@.service".split(" "))
    return scp, mv, serv, mvserv


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--update_rippled", action="store_true")
    parser.add_argument("--reset_network", action="store_true")
    parser.add_argument("--update_and_reset_network", action="store_true")
    parser.add_argument("--restart_rippled_after_install", action="store_true")
    parser.add_argument("--check_release_needed", action="store_true")
    parser.add_argument("--check_latest", action="store_true")
    parser.add_argument("--default", action="store_true", help="The db and log will be updated at the default locations. i.e. /var/lib and /var/log")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    breakpoint()
    if not args.default:
        DB_PATH = AMM_DB_PATH
        LOG_PATH = AMM_LOG_PATH
    if args.restart_rippled_after_install:
        restart = True
    if args.update_rippled:
        logging.info("Updating rippled...")
        update_rippled(restart=restart)
    elif args.reset_network:
        logging.info("Resetting network...")
        # reset_network()
    elif args.update_and_reset_network:
        logging.info("Updating rippled and resetting network...")
        update_rippled(reset_network=True, restart=restart)

    if args.check_release_needed:
        if release_needed():
            logging.info("Need to build release")
            print("true") # printed for consumption by github action step output
        else:
            logging.info("Release up to date")

    if args.check_latest:
        if not os.path.exists(GITREV_FILE):
            if not os.path.exists(RIPPLED_INSTALL_PATH):
                logging.info("rippled must not be installed!")
                os.mkdir(RIPPLED_INSTALL_PATH)
            write_gitrev_file()

        try:
            latest_release = get_latest_release_version()
            version = get_installed_version()
            if version != latest_release or latest_release != check_output(['cat', GITREV_FILE]).decode():
                    dl_latest()
                    restart_rippled()
            else:
                logging.info(f'Local install {version} matches latest release {latest_release}')
        except Exception as e:
            logging.warning(e)
