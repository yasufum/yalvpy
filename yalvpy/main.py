#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et :

import argparse
import os
import re
import shutil
import subprocess
import sys
from xml.etree import ElementTree as et

# TODO(yasufum): Revise how manage constants.
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

# clone-vms.sh, remove-vms.sh
VOL_PREFIX = "{}{}{}{}".format(DISTRO, DIST_VER[0], DIST_VER[1], DIST_VER[2])

# Required commands for running this tool.
REQUIRED_CMDS = ["virsh", "virt-install", "virt-clone", "virt-customize",
                 "virt-sysprep"]


def message(msg):
    print("[command] {}".format(msg))


def _check_required_cmds():
    '''Check if require commands are installed'''

    missing_cmds = []
    for c in REQUIRED_CMDS:
        if shutil.which(c) is None:
            missing_cmds.append(c)

    if missing_cmds:
        print("Error: You're required to install the tools below for "
              "running this application.")
        print("  {}".format('  '.join(missing_cmds)))
        sys.exit(1)


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

    # list subcommand
    p_list = sp.add_parser("list", help="show list of vms")
    p_list.set_defaults(func=list)

    # ssh subcommand
    p_ssh = sp.add_parser("ssh", help="login to a host")
    p_ssh.add_argument("destination")
    p_ssh.add_argument("command", type=str, nargs='*')
    p_ssh.set_defaults(func=ssh)

    # net subcommand
    p_dhcp_host = sp.add_parser("dhcp-host", help="update static IP address of dhcp")
    p_dhcp_host.add_argument("command", help="'add', 'delete' or 'modify'")
    p_dhcp_host.add_argument("hostname", help="hostname")
    p_dhcp_host.add_argument("ip", help="IP address", nargs='?')
    p_dhcp_host.add_argument("-n", "--network", type=str, default="default",
                             help="The name of network managed by libvirt")
    p_dhcp_host.add_argument("--mac", help="specify mac address instead of "
                             "retrieving from DHCP entry")
    p_dhcp_host.add_argument(
        "--dry-run", action="store_true", help="Show the command, but do nothing")
    p_dhcp_host.set_defaults(func=update_dhcp_host)

    return p


def install(args):
    diskname = f"{args.name}.{IMG_EXT}"
    cmd = [
        "sudo",
        "virt-install",
        "--name", args.name,
        "--ram", str(args.ram),
        "--disk", f"path={args.img_dir}/{diskname},size={args.disk_size}",
        "--vcpus", str(args.vcpus),
        "--os-variant", OS_VARIANT,
        "--network", f"bridge={NW_BRIDGE}",
        "--graphics", "none",
        "--console", "pty,target_type=serial",
        "--location", f"{LOCATION},kernel=casper/vmlinuz,initrd=casper/initrd",
        "--extra-args", 'console=ttyS0,115200n8'
    ]

    if args.dry_run is not True:
        message(" ".join(cmd))
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


def _net_dhcp_leases(network="default"):
    '''Return a list of DHCP entries

    The bunch of entries is retrieved with `virsh net-dhcp-leases` command.
    '''

    cmd = ["sudo", "virsh", "net-dhcp-leases", network]
    entries = (subprocess.check_output(cmd, text=True)).split("\n")
    res = []
    for i in range(2, len(entries)):
        params = (re.sub("\\s+", " ", entries[i])).split(" ")
        if len(params) == 8:
            res.append({
                "expiry_time": "{} {}".format(params[1], params[2]),
                "mac": params[3],
                "proto": params[4],
                "ipaddr": params[5].split("/")[0],
                "hostname": params[6],
                "id": params[7]
                })
    return res


def list(args):
    # Print header
    # print("hostname\tipaddr")

    for ent in _net_dhcp_leases():
        print(f"{ent["hostname"]}\t{ent["ipaddr"]}")


def ssh(args):
    user = os.environ["USER"]
    dest = args.destination.split("@")
    if len(dest) == 2:
        user = dest[0]
        hostname = dest[1]
    elif len(dest) == 1:
        hostname = dest[0]
    else:
        print(f"Error: Invalid destination {args.destination!r}.")
        sys.exit()

    cmd = []
    for ent in _net_dhcp_leases():
        if hostname == ent["hostname"]:
            cmd = ["ssh", f'{user}@{ent["ipaddr"]}']
            if args.command is not None:
                cmd.append(' '.join(args.command))
            break
    
    subprocess.run(cmd)


def update_dhcp_host(args):
    section = "ip-dhcp-host"

    cmd = ["sudo", "virsh", "net-update", args.network, args.command, section]

    mac = None
    for ent in _net_dhcp_leases():
        if ent["hostname"] == args.hostname:
            mac = ent["mac"]

    if args.command == "add":
        cmd.append("<host mac=\"{}\" ip=\"{}\"/>".format(mac, args.ip))

    elif args.command == "delete" or args.command == "modify":
        ipaddr = None
        cmd_xml = ["sudo", "virsh", "net-dumpxml", args.network]
        entries = (subprocess.check_output(cmd_xml, text=True))
        xmlent = et.fromstring(entries)
        try:
            for elem in xmlent.findall("./ip/dhcp/host"):
                if mac == elem.get("mac"):
                    if args.command == "delete":
                        ipaddr = elem.get("ip")
                    else:
                        ipaddr = args.ip

                elif args.mac == elem.get("mac"):
                    if args.command == "delete":
                        ipaddr = elem.get("ip")
                    else:
                        ipaddr = args.ip
                    mac = args.mac

            if ipaddr is None:
                print("FAILED: MAC address {!r} of host {!r}".format(
                        mac, args.hostname),
                      "not found in the net definition.",
                      "You can find the address with `virsh net-dumpxml {}`".format(args.network),
                      "and specify with --mac option.")
                sys.exit(1)
        except Exception as e:
            print("Error: Parsing XML failure for - {}".format(e))

        cmd.append("<host mac=\"{}\" ip=\"{}\"/>".format(mac, ipaddr))

    else:
        print("Error: Invalid command {!r}.".format(args.method))
        sys.exit(1)

    cmd.append("--live")
    cmd.append("--config")

    if args.dry_run is not True:
        message(" ".join(cmd))
        subprocess.run(cmd)
    else:
        message(" ".join(cmd))


def main():
    _check_required_cmds()

    p = get_parser()
    args = p.parse_args()
    if args == argparse.Namespace():
        p.parse_args(['--help'])
    else:
        args.func(args)

if __name__ == "__main__":
    main()
