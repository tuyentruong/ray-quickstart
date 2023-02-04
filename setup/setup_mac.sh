cd ~/git/ray-quickstart

brew install miniconda
conda update -n base -c defaults conda -y

conda init bash
conda config --set auto_activate_base  false

conda create -n ray-quickstart python=3.9.12 -y

source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh
conda activate ray-quickstart

conda install pipenv -y

# install conda version to get version of grpc that works with Macs
conda install grpcio=1.43.0 -y

pipenv install --python="$(which python)" --site-packages

# now copy grpc from conda's site-packages to the pipenv's site-packages
cp -R /opt/homebrew/Caskroom/miniconda/base/envs/ai/lib/python3.9/site-packages/grpc $(pipenv --venv)/lib/python3.9/site-packages/
