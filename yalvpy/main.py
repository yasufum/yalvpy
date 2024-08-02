#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et :

import argparse
import subprocess

# TODO: Revise how manage constants.
DISTRO = "ubuntu"
DIST_VER = ("22", "04", "4")
IMG_DIR = "/var/lib/libvirt/images"
NW_BRIDGE = "virbr0"
IMG_EXT = "qcow2"

ORIG_VMNAME = f"{DISTRO}-orig"
OS_VARIANT = "{}{}.{}".format(DISTRO, DIST_VER[0], DIST_VER[1])
ISO_IMG = "{}-{}.{}.{}-live-server-amd64.iso".format(
        DISTRO, DIST_VER[0], DIST_VER[1], DIST_VER[2])
LOCATION = f"{IMG_DIR}/{ISO_IMG}"

DISK_NAME = f"{ORIG_VMNAME}.{IMG_EXT}"

# clone-vms.sh, remove-vms.sh
VOL_PREFIX = "{}{}{}{}".format(DISTRO, DIST_VER[0], DIST_VER[1], DIST_VER[2])


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
        help="name of guest instance")
    p_inst.add_argument(
        "--ram", type=int,
        help="mem size in MiB (default is {})".format(1024*8), default=1024*8)
    p_inst.add_argument("--img-dir", type=str, default=IMG_DIR,
                        help=f"libvirt image dir (default is {IMG_DIR})")
    p_inst.add_argument("--img", type=str, default=ISO_IMG,
                        help=f"the name of ISO image (default is {ISO_IMG})")
    p_inst.add_argument(
        "--disk-size", type=int, default=200,
        help="the size of volume (default is 200)")
    p_inst.add_argument(
        "--vcpus", type=int, default=8,
        help="the num of CPUs (default is 8)" )
    p_inst.add_argument(
        "--dry-run", action="store_true", help="show the command, but do nothing")
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
        "--disk", f"path={args.img_dir}/{DISK_NAME},size={args.disk_size}",
        "--vcpus", str(args.vcpus),
        "--os-variant", OS_VARIANT,
        "--network", f"bridge={NW_BRIDGE}",
        "--graphics", "none",
        "--console", "pty,target_type=serial",
        "--location", f"{LOCATION},kernel=casper/vmlinuz,initrd=casper/initrd",
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
