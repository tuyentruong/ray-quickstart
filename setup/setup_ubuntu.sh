#!/bin/bash
# install Python
set -x

sudo apt update -y
sudo apt install python3 python3-pip -y
curl https://repo.anaconda.com/archive/Anaconda3-2021.11-Linux-x86_64.sh --output ~/anaconda.sh
chmod +x ~/anaconda.sh
~/anaconda.sh -b
rm ~/anaconda.sh
~/anaconda3/bin/conda update -n base -c defaults conda -y

~/anaconda3/bin/conda init bash
~/anaconda3/bin/conda config --set auto_activate_base  false

# clone repos
mkdir -p ~/git
cd ~/git
ssh-keyscan github.com > ~/.ssh/known_hosts
git clone https://github.com/tuyentruong/ray-quickstart.git ~/git/ray-quickstart

cd ~/git/ray-quickstart
~/anaconda3/bin/conda create -n ray-quickstart python=3.9.12 -y
source ~/anaconda3/etc/profile.d/conda.sh
conda activate ray-quickstart
~/anaconda3/bin/conda install pipenv -y

# add autoenv
curl -#fLo- 'https://raw.githubusercontent.com/hyperupcall/autoenv/master/scripts/install.sh' | sh -s -- -y

sudo cp -R ~/git/ray-quickstart/setup/ubuntu/* /
sudo sed -i "s/USER/$USER/" /etc/systemd/system/ray-cluster.service

sudo apt install openssh-server net-tools -y

# install dlib dependencies
sudo apt install build-essential cmake pkg-config -y
sudo apt install libx11-dev libatlas-base-dev -y
sudo apt install libgtk-3-dev libboost-python-dev -y

# install Python packages for ML/AI
pipenv install --python="/home/$USER/anaconda3/envs/ray-quickstart/bin/python" --site-packages

# install CUDA
cd ~
sudo apt-key del 7fa2af80
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/sbsa/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.0.0/local_installers/cuda-repo-ubuntu2204-12-0-local_12.0.0-525.60.13-1_arm64.deb
sudo dpkg -i cuda-repo-ubuntu2204-12-0-local_12.0.0-525.60.13-1_arm64.deb
rm -f cuda-repo-ubuntu2204-12-0-local_12.0.0-525.60.13-1_arm64.deb
sudo cp /var/cuda-repo-ubuntu2204-12-0-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update -y
sudo apt-get -y install cuda nvidia-cuda-toolkit

sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get -y install nvidia-driver-525 nvidia-dkms-525

sudo systemctl enable --now ray-cluster.service

# setup .bashrc
if ! grep -Fq "AUTOENV_ASSUME_YES" ~/.bashrc
then
  echo 'export AUTOENV_ASSUME_YES=1' >> ~/.bashrc
  echo 'export AUTOENV_ENABLE_LEAVE=1' >> ~/.bashrc
  echo 'export AUTOENV_ENV_FILENAME=.autoenv' >> ~/.bashrc
  echo 'export AUTOENV_ENV_LEAVE_FILENAME=.autoenv.leave' >> ~/.bashrc
  echo '' >> ~/.bashrc
  echo 'export EDITOR=vim' >> ~/.bashrc
  echo 'export LD_LIBRARY_PATH=/usr/lib/wsl/lib' >> ~/.bashrc
  echo '' >> ~/.bashrc
  echo 'export PATH=~/anaconda3/bin:${PATH}:/usr/lib/wsl/lib' >> ~/.bashrc
fi
