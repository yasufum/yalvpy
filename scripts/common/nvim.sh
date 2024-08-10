#!/bin/bash

TARGET_DIR=/usr/local
DOWNLOAD=https://github.com/neovim/neovim/releases/latest/download/nvim-linux64.tar.gz
ZIP=$(echo ${DOWNLOAD} | awk -F'/' '{print $NF}')
NVIM_DIR=$(echo ${ZIP} | awk -F'.' '{print $1}')

wget ${DOWNLOAD}
sudo tar zxvf ${ZIP} -C ${TARGET_DIR}

rm ${ZIP}
echo "export PATH=${TARGET_DIR}/${NVIM_DIR}/bin:"'$PATH' >> $HOME/.bashrc
