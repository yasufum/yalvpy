#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: fenc=utf-8 ff=unix ft=python ts=4 sw=4 sts=4 si et :

import argparse
import os
import re
import shutil
import subprocess
import sys
import typer
from typing import Annotated
from typing import List
from typing import Optional
import urllib.error
from urllib import request
from xml.etree import ElementTree as et

# TODO(yasufum): Revise how manage constants.
IMG_EXT = "qcow2"
IMG_DIR = "/var/lib/libvirt/images"

VOL_PREFIX = "yalvpy"

# Required commands for running this tool.
REQUIRED_CMDS = ["virsh", "virt-install", "virt-clone", "virt-customize",
                 "virt-sysprep", "osinfo-query"]


app = typer.Typer()

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


@app.command()
def install(
    name: str = typer.Argument(help="Name of the guest instance."),
    osinfo: Annotated[
        str,
        typer.Option(
            '--osinfo',
            help="Optimize guest config for a specific OS. All the list can bereferred from 'osinfo-query os'.")
    ] = None,
    os_variant: Annotated[
        str,
        typer.Option(
            '--os-variant',
            help="The OS being install in the guest. Use 'virt-install --osinfo list' to see the full list.")
    ] = None,
    memory: Annotated[
        int,
        typer.Option(
            '--memory',
            help="Memory size in MiB.",
            )
    ] = 1024*8,
    img_dir: Annotated[
        str,
        typer.Option(
            '--img-dir',
            help="libvirt image dir.",
            )
    ] = IMG_DIR,
    disk_size: Annotated[
        int,
        typer.Option(
            '--disk-size',
            help="The size of volume.",
            )
    ] = 200,
    vcpus: Annotated[
        int,
        typer.Option(
            '--vcpus',
            help="The number of CPUs.",
            )
    ] = 8,
    network: Annotated[
        str,
        typer.Option(
            '--network',
            help="Configure a guest network interface.",
            )
    ] = "network=default",
    location: Annotated[
        str,
        typer.Option(
            '--location',
            help="Distro install URL or file path of image.",
            )
    ] = ...,
    dry_run: Annotated[
        bool,
        typer.Option('--dry-run', help="Show the command, but do nothing.")
    ] = False,
):
    diskname = f"{VOL_PREFIX}-{name}.{IMG_EXT}"

    cmd = [
        "sudo",
        "virt-install",
        "--name", name,
        "--memory", str(memory),
        "--disk",
        "path={}/{},size={},format={}".format(
            img_dir, diskname, disk_size, IMG_EXT),
        "--vcpus", str(vcpus),
        "--network", network,
        "--graphics", "none",
        "--console", "pty,target_type=serial",
        "--extra-args", 'console=ttyS0,115200n8'
    ]

    # OS option can be specified with `--os-variant` or `--osinfo`.
    # Use --os-variant and discard --osinfo if both are given.
    os_opt = None   # --os-variant or --osinfo
    os_opt_arg = None
    if os_variant is not None:
        os_opt = "--os-variant"
        os_opt_arg = os_variant
    elif osinfo is not None:
        os_opt = "--osinfo"
        os_opt_arg = osinfo

    if os_opt is not None:
        def _is_os_opt_valid():
            osiq_cmd = ["osinfo-query", "os", "-f", "short-id"]
            oslist = subprocess.run(
                osiq_cmd, encoding='utf-8', stdout=subprocess.PIPE)
            flg = False
            for osinfo in oslist.stdout.split("\n"):
                if os_opt_arg == osinfo.strip():
                    flg = True
                    break
            if flg is not True:
                print(f"Error: OS option {os_opt_arg!r} not found.")
                sys.exit(1)

        _is_os_opt_valid()
        cmd.append(os_opt)
        cmd.append(os_opt_arg)

    try:
        if not (os.path.isfile(location) or request.urlopen(location)):
            print(f"Error: Invalid location {location!r}.")
            exit(1)
    except urllib.error.HTTPError:
        print(f"Error: Invalid URL {location!r}.")
        exit(1)
    except ValueError:
        print(f"Error: Invalid file path {location!r}.")
        exit(1)

    cmd.append("--location")
    ubuntu_extra_opt = "kernel=casper/vmlinuz,initrd=casper/initrd"
    if "ubuntu" in str(os_opt_arg):
        cmd.append(f"{location},{ubuntu_extra_opt}")
    elif "ubuntu" in location.lower():
        print("Guessing guest distro is Ubuntua and adding extra params "
            f"{ubuntu_extra_opt!r} to --location option")
        cmd.append(f"{location},{ubuntu_extra_opt}")
    else:
        cmd.append(location)

    if dry_run is not True:
        message(" ".join(cmd))
        subprocess.run(cmd)
    else:
        message(" ".join(cmd))


@app.command()
def clone(
    names: List[str] = typer.Argument(
       ..., help="Name of cloned VM, or several ones separaed by a white space."),
    original: Annotated[
      str,
      typer.Option('-o', '--original', help="Name of original VM.")
    ] = ...,
    fpath: Annotated[
      str,
      typer.Option('-f', '--file', help="Filepath of volume of the cloned VM.")
    ] = None,
    img_dir: Annotated[
      str,
      typer.Option('-i', '--img-dir',
                   help="libvirt image dir.")
    ] = IMG_DIR,
    dry_run: Annotated[
      bool,
      typer.Option('--dry-run', help="Show the command, but do nothing.")
    ] = False,
    ):
    for name in names:
        if fpath is None:
            fname = "{}/{}-{}.{}".format(img_dir, VOL_PREFIX, name, IMG_EXT)
        else:
            fname = fpath

        cmds = [
            [
                "sudo",
                "virt-clone",
                "--original", original,
                "--name", name,
                "--file", fname,
            ],
            # NOTE: hostname can also be changed by using `virt-sysprep`, but
            # cause an unexpected another change by which sshd cannot be launched.
            ["sudo", "virt-customize", "-d", name, "--hostname", name,],
            ["sudo", "virt-sysprep", "-d", name, "--enable", "machine-id",],
            ["sudo", "virsh", "start", name,],
        ]

        try:
            for cmd in cmds:
                if dry_run is not True:
                    message(" ".join(cmd))
                    subprocess.run(cmd, check=True)
                else:
                    message(" ".join(cmd))
        except subprocess.CalledProcessError as e:
            if e.cmd[0] == "virt-clone" or e.cmd[1] == "virt-clone":
                ans = input("You cannot clone from a running VM."
                            f"Shutdown '{original}'? [y/N]\n")
                if ans.lower() == "y" or ans.lower() == "yes":
                    subprocess.run(["sudo", "virsh", "shutdown", original,])
                    print("Try again after the VM is down.")
            else:
                # Don't care other than a failure of virt-clone.
                pass


@app.command()
def remove(
    names: List[str] = typer.Argument(
       ..., help="Name of removed VM, or several ones separaed by a white space."),
    fpath: Annotated[
        str,
        typer.Option('-f', '--file', help="Filepath of volume of the removed VM.")
    ] = None,
    img_dir: Annotated[
        str,
        typer.Option('-i', '--img-dir',
                     help="libvirt image dir.")
    ] = IMG_DIR,
    dry_run: Annotated[
        bool,
        typer.Option('--dry-run', help="Show the command, but do nothing.")
    ] = False,
):
    for name in names:
        if fpath is None:
            fname = "{}/{}-{}.{}".format(img_dir, VOL_PREFIX, name, IMG_EXT)
        else:
            fname = fpath

        cmds = [
            ["sudo", "virsh", "shutdown", name,],
            ["sudo", "virsh", "undefine", name,],
            ["sudo", "rm", fname],
        ]
        if dry_run is not True:
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


@app.command()
def list():

    for ent in _net_dhcp_leases():
        print("{}\t{}".format(ent["hostname"],ent["ipaddr"]))


@app.command()
def ssh(
    destination: str = typer.Argument(help="Destination host."),
    command: Optional[List[str]] = typer.Argument(
        None, help="A command run on the destination."),
):
    user = os.environ["USER"]
    dest = destination.split("@")
    if len(dest) == 2:
        user = dest[0]
        hostname = dest[1]
    elif len(dest) == 1:
        hostname = dest[0]
    else:
        print(f"Error: Invalid destination {destination!r}.")
        sys.exit()

    cmd = []
    for ent in _net_dhcp_leases():
        if hostname == ent["hostname"]:
            cmd = ["ssh", f'{user}@{ent["ipaddr"]}']
            if command is not None:
                cmd.append(' '.join(command))
            break
    
    if not cmd:
        print(f"Error: No hostname matched {hostname!r}.")
        sys.exit()
    subprocess.run(cmd)


@app.command()
def dhcp_host(
    command: str = typer.Argument(help="'add', 'delete' or 'modify'."),
    hostname: str = typer.Argument(help="hostname."),
    ip: str = typer.Argument(help="IP address."),
    network: Annotated[
        str,
        typer.Option('-n', '--network', help="Name of network managed by libvirt.")
    ] = "default",
    mac: Annotated[
        str,
        typer.Option('--mac', help="Specify MAC address instead of retrieving from DHCP entry.")
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option('--dry-run', help="Show the command, but do nothing.")
    ] = False,
):
    section = "ip-dhcp-host"

    cmd = ["sudo", "virsh", "net-update", network, command, section]

    mac = None
    for ent in _net_dhcp_leases():
        if ent["hostname"] == hostname:
            mac = ent["mac"]

    if command == "add":
        cmd.append("<host mac=\"{}\" ip=\"{}\"/>".format(mac, ip))

    elif command == "delete" or command == "modify":
        ipaddr = None
        cmd_xml = ["sudo", "virsh", "net-dumpxml", network]
        entries = (subprocess.check_output(cmd_xml, text=True))
        xmlent = et.fromstring(entries)
        try:
            for elem in xmlent.findall("./ip/dhcp/host"):
                if mac == elem.get("mac"):
                    if command == "delete":
                        ipaddr = elem.get("ip")
                    else:
                        ipaddr = ip

                elif mac == elem.get("mac"):
                    if command == "delete":
                        ipaddr = elem.get("ip")
                    else:
                        ipaddr = ip
                    mac = mac

            if ipaddr is None:
                print("FAILED: MAC address {!r} of host {!r}".format(
                        mac, hostname),
                      "not found in the net definition.",
                      "You can find the address with `virsh net-dumpxml {}`".format(network),
                      "and specify with --mac option.")
                sys.exit(1)
        except Exception as e:
            print("Error: Parsing XML failure for - {}".format(e))

        cmd.append("<host mac=\"{}\" ip=\"{}\"/>".format(mac, ipaddr))

    else:
        print("Error: Invalid command {!r}.".format(command))
        sys.exit(1)

    cmd.append("--live")
    cmd.append("--config")

    if dry_run is not True:
        message(" ".join(cmd))
        subprocess.run(cmd)
    else:
        message(" ".join(cmd))


def main():
    _check_required_cmds()
    app()

if __name__ == "__main__":
    main()
