# yalvpy

Yet another virsh wrapper implemented in python.

## Usage

Currently the following subcommands are supported.

* `install`: runs `virt-install` for launching a new VM.
* `clone`: creates new VMs from a originl template VM. 
* `remove`: shutdown VMs and delete domains and disk files.
* `list`: show a list of a set of hostname and IP address of each guest.
* `dhcp-host`: update static IP address of dhcp
* `ssh`: naive ssh client to enable to login with hostname
  instead of IP address.

For example, run `install` after installing this tool via `pip`.

```sh
# Run virt-install with the default params such as vpus or mem .
$ yalvpy install VMNAME
```

You can run `install` from `yalvpy/main.py` without installing as below.
A `VMNAME` corresponds to a domain of libvirt.

```sh
$ python3 yalvpy/main.py install VMNAME
```


## Required packages

* qemu-kvm
* libvirt
* virsh
* virt-install
* guestfish (libguestfs-tools)

You can install all the packages above by following the installation.

```sh
sudo apt install qemu-kvm libvirt-daemon-system \
     virtinst libguestfs-tools
```

## For developers

### Setup

This tool provides pip installation with `setuptools` and it can be setup
by `venv`.

```sh
$ git clone https://github.com/yasufum/yalvpy.git
$ pyhton3 -m venv yalvpy
```

Install the package in editable mode at the project root.

```sh
$ cd yalvpy
$ pip3 install -e .
```
