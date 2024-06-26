#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et :

import argparse
import subprocess

# TODO: Revise how manage constants.
ORIG_VMNAME = "ubuntu2204"
IMG_DIR = "/var/lib/libvirt/images"
IMG_EXT = "qcow2"
OS_VARIANT = "ubuntu22.04"
NW_BRIDGE = "virbr0"
ISO_IMG = "ubuntu-22.04.3-live-server-amd64.iso"

DISK_NAME = "{}.{}".format(ORIG_VMNAME, IMG_EXT)
LOCATION = "{}/{}".format(IMG_DIR, ISO_IMG)

# clone-vms.sh, remove-vms.sh
VOL_PREFIX = "ubuntu2204"


def message(msg):
    print("[command] {}".format(msg))


# TODO: Revise help messages.
def get_parser():
    p = argparse.ArgumentParser(description="virsh manager")
    sp = p.add_subparsers(
        title="subcommands", description="subcommand description")

    # install subcommand
    p_inst = sp.add_parser("install", help="install vm")
    p_inst.add_argument(
        "name", type=str, default=ORIG_VMNAME,
        help="Name of guest instance")
    p_inst.add_argument(
        "--ram", type=int,
        help="Mem size in MiB (default is {})".format(1024*8), default=1024*8)
    p_inst.add_argument("--img-dir", type=str, default=IMG_DIR,
                        help="libvirt image dir (default is {})".format(IMG_DIR))
    p_inst.add_argument(
        "--disk-name", type=str, default=DISK_NAME,
        help="The name of image file")
    p_inst.add_argument(
        "--disk-size", type=int, default=200,
        help="The size of volume")
    p_inst.add_argument(
        "--vcpus", type=int, help="The num of CPUs", default=8)
    p_inst.add_argument(
        "--dry-run", action="store_true", help="Show the command, but do nothing")
    p_inst.set_defaults(func=install)

    # clone subcommand
    p_clone = sp.add_parser("clone", help="clone vm")
    p_clone.add_argument("name", type=str, nargs="+",
                         help="Name of cloned VM")
    p_clone.add_argument(
        "--dry-run", action="store_true", help="Show the command, but do nothing")
    p_clone.add_argument(
        "--original", type=str, help="Name of original VM", default=ORIG_VMNAME)
    p_clone.add_argument(
        "--file", type=str, help="(Optional) Filepath of volume of the cloned VM")
    p_clone.set_defaults(func=clone)

    # remove subcommand
    p_rm = sp.add_parser("remove", help="remove vm")
    p_rm.add_argument("name", type=str, nargs="+",
                      help="Name of a VM removed")
    p_rm.add_argument(
        "--dry-run", action="store_true", help="Show the command, but do nothing")
    p_rm.add_argument(
        "--file", type=str, help="(Optional) Filepath of volume of the removed VM")
    p_rm.set_defaults(func=remove)

    return p


def install(args):
    cmd = [
        "sudo",
        "virt-install",
        "--name", args.name,
        "--ram", str(args.ram),
        "--disk", "path={}/{},size={}".format(args.img_dir, args.disk_name, args.disk_size),
        "--vcpus", str(args.vcpus),
        "--os-variant", OS_VARIANT,
        "--network", "bridge={}".format(NW_BRIDGE),
        "--graphics", "none",
        "--console", "pty,target_type=serial",
        "--location", "{},kernel=casper/vmlinuz,initrd=casper/initrd".format(LOCATION),
        "--extra-args", 'console=ttyS0,115200n8'
    ]

    if args.dry_run is not True:
        subprocess.run(cmd)
    else:
        message(" ".join(cmd))


def clone(args):
    for name in args.name:
        if args.file is None:
            fname = "{}/{}-{}.{}".format(IMG_DIR, VOL_PREFIX, name, IMG_EXT)
        else:
            fname = args.file

        cmds = [
            [
                "sudo",
                "virt-clone",
                "--original", args.original,
                "--name", name,
                "--file", fname,
            ],
            # NOTE: hostname can also be changed by using `virt-sysprep`, but
            # cause an unexpected another change by which sshd cannot be launched.
            ["sudo", "virt-customize", "-d", name, "--hostname", name,],
            ["sudo", "virt-sysprep", "-d", name, "--enable", "machine-id",],
            ["sudo", "virsh", "start", name,],
        ]

        for cmd in cmds:
            if args.dry_run is not True:
                message(" ".join(cmd))
                subprocess.run(cmd)
            else:
                message(" ".join(cmd))


def remove(args):
    for name in args.name:
        if args.file is None:
            fname = "{}/{}-{}.{}".format(IMG_DIR, VOL_PREFIX, name, IMG_EXT)
        else:
            fname = args.file

        cmds = [
            ["sudo", "virsh", "shutdown", name,],
            ["sudo", "virsh", "undefine", name,],
            ["sudo", "rm", fname],
        ]
        if args.dry_run is not True:
            for cmd in cmds:
                message(" ".join(cmd))
                subprocess.run(cmd)
        else:
            for cmd in cmds:
                message(" ".join(cmd))


def main():
    p = get_parser()
    args = p.parse_args()
    if args == argparse.Namespace():
        p.parse_args(['--help'])
    else:
        args.func(args)

if __name__ == "__main__":
    main()
