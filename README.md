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
yalvpy install VMNAME
```

You can run `install` from `yalvpy/main.py` without installing as below.
A `VMNAME` corresponds to a domain of libvirt.

```sh
python3 yalvpy/main.py install VMNAME
```


## Required packages

* qemu-kvm
* libvirt
* virsh
* virt-install
* guestfish (libguestfs-tools)
* python3-venv
* python3-pip

You can install all the packages above by following the installation.

```sh
sudo apt install qemu-kvm libvirt-daemon-system \
     virtinst libguestfs-tools \
     python3-venv python3-pip
```

## For developers

### Setup

This tool provides pip installation with `setuptools` and it can be setup
by `venv`.

```sh
git clone https://github.com/yasufum/yalvpy.git
pyhton3 -m venv yalvpy
```

Install the package in editable mode at the project root.

```sh
cd yalvpy
. bin/activate
pip3 install -e .
```

### Tips

#### Add sudoers for running a command without password

Before running a script using `sudo`, you should add your account to sudoers.
Add a sudoers file for your account as `/etc/sudoers.d/USER`. If you have
an account `user`, the contents of sudoers file is like as following.

```
# /etc/sudoers.d/user
user ALL=(ALL) NOPASSWD: ALL
```

#### Upload your ssh-key on a guest

```sh
ssh-copy-id -i $HOME/.ssh/id_ed25519.pub user@guest
```

#### Create stack user for devstack

```sh
ssh user@guest 'bash -s' < scripts/openstack/setup-stack-user.sh
```

#### Install neovim

Install the latest neovim.

```sh
ssh user@guest 'bash -s' < scripts/common/nvim.sh
```

It's recommended to install
[LunarVim](https://www.lunarvim.org/)
to setup your dev environment easily.

You'd install depending tools before LunarVim.

* gcc
* make
* unzip
```sh
apt install gcc make unzip
```

* npm (https://nodejs.org/en/download/package-manager)

```sh
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
nvm install 22
```

* rust
```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

For LunarVim, just Run the install script below.

```sh
bash <(curl -s https://raw.githubusercontent.com/lunarvim/lunarvim/master/utils/installer/install.sh)
```
