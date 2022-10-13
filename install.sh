#!/bin/bash

set -ex

SYSTEMD_DIR="/etc/systemd/system/"
UPDATER_DIR="/opt/amm_updater/"

mkdir -p $UPDATER_DIR
cp amm_update.py $UPDATER_DIR
cp amm_updater.timer $SYSTEMD_DIR
cp amm_updater.service $SYSTEMD_DIR

systemctl enable amm_updater.timer
systemctl enable amm_updater.service

systemctl start amm_updater.timer
systemctl start amm_updater.service
