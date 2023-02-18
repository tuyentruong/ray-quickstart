#!/bin/bash

brew install miniconda
conda update -n base -c defaults conda -y

conda init bash
conda config --set auto_activate_base false
source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh

cd ~/git/ray-quickstart
python3 setup.py install_env

source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh
conda activate ray-quickstart
