#!/bin/bash

source $(dirname $0)/vars.sh

# NOTE: Use `--location` instead of `--cdrom` because `--extra-args` for none
# graphical install via console cannot accept `--cdrom`.

# https://releases.ubuntu.com/jammy/
# https://releases.ubuntu.com/jammy/ubuntu-22.04.3-live-server-amd64.iso
LOCATION=${IMG_DIR}/ubuntu-22.04.3-live-server-amd64.iso
OS_VARIANT=ubuntu22.04

sudo virt-install \
--name ${ORIG_VMNAME} \
--ram ${MEM} \
--disk path=${IMG_DIR}/${DISK_NAME},size=${DISK_SIZE} \
--vcpus ${VCPUS} \
--os-variant ${OS_VARIANT} \
--network bridge=${NW_BRIDGE} \
--graphics none \
--console pty,target_type=serial \
--location ${LOCATION},kernel=casper/vmlinuz,initrd=casper/initrd \
--extra-args 'console=ttyS0,115200n8'
