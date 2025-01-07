#!/bin/bash

# Get Latest release
RELEASE="$(curl -sSL https://dl.k8s.io/release/stable.txt)"
echo "Download Kubernetes tools [Release $RELEASE]"


# Forwarding IPv4 and letting iptables see bridged traffic 
# https://kubernetes.io/docs/setup/production-environment/container-runtimes/#forwarding-ipv4-and-letting-iptables-see-bridged-traffic
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

# sysctl params required by setup, params persist across reboots
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

# Apply sysctl params without reboot
sudo sysctl --system

# Update
sudo apt-get update -y
sudo install -m 0755 -d /etc/apt/keyrings

# Install requirements
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    apt-transport-https \
    nfs-common

# Kubernetes Repository
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Docker (Containerd) Repository
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update
sudo apt-get update

# Install Kubernetes and lock the version
sudo apt-get install -y kubectl kubelet kubeadm
sudo apt-mark hold kubelet kubeadm kubectl

# Install containerd
sudo apt-get install containerd.io -y

# https://github.com/containerd/containerd/issues/4581
#sudo systemctl start containerd
#sudo rm -f /etc/containerd/config.toml

sudo mv /etc/containerd/config.toml /etc/containerd/config.toml.orig
containerd config default | sudo tee /etc/containerd/config.toml
sudo sed -i 's/SystemdCgroup \= false/SystemdCgroup \= true/g' /etc/containerd/config.toml
sudo systemctl restart containerd
sudo systemctl enable containerd

# Install CNI Plugin
CNI_PLUGINS_VERSION="v1.6.1"
ARCH="amd64"
DEST="/opt/cni/bin"
sudo mkdir -p "$DEST"
curl -L "https://github.com/containernetworking/plugins/releases/download/${CNI_PLUGINS_VERSION}/cni-plugins-linux-${ARCH}-${CNI_PLUGINS_VERSION}.tgz" | sudo tar -C "$DEST" -xz

# Install nerdctl
NERDCTL_VER=2.0.2
NERDCTL_TGZ=nerdctl-${NERDCTL_VER}-linux-${ARCH}.tar.gz
wget https://github.com/containerd/nerdctl/releases/download/v${NERDCTL_VER}/${NERDCTL_TGZ}
sudo tar Cxzvf /usr/local/bin ${NERDCTL_TGZ}

sudo swapoff -a
sudo rm -f /swap.img

echo "Finished."
