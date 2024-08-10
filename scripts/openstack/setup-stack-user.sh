#!/bin/bash

sudo useradd -s /bin/bash -d /opt/stack -m stack
echo "stack ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/stack

# Permission of `stack` directory is 0700 on CentOS 8, but it cause an
# error in a sanity check for the permission while running devstack
# installatino.
sudo chmod 755 /opt/stack

sudo mkdir -p /opt/stack/.ssh
sudo chown -R stack:stack /opt/stack/.ssh
