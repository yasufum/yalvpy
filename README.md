# lvpy

Yet another libvirt wrapper implemented in python.

## Usage

Currently the following subcommands are supported.

* `install`: runs `virt-install` for launching a new VM.
* `clone`: creates new VMs from a originl template VM. 
* `remove`: shutdown VMs and delete domains and disk files.

For example, you can run `install` from `lvpy/main.py` as below.
A `VMNAME` corresponds to a domain of libvirt.

```sh
$ python3 lvpy/main.py install VMNAME
```

Or just run with the main command after install via `pip`.

```sh
$ lvpy install VMNAME
```

## For developers

### Setup

This tool provides pip installation with `setuptools` and it can be setup
by `venv`.

```sh
$ git clone https://github.com/yasufum/lvpy.git
$ pyhton3 -m venv lvpy
```

Install the package in editable mode at the project root.

```sh
$ cd lvpy
$ pip3 install -e .
```
