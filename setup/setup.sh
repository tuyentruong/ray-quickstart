cd ~/git/ai

brew install miniconda
conda init bash

conda create -n ray-quickstart python=3.9.12 -y

source activate ray-quickstart

conda install pipenv build twine -y

pipenv install --python 3.9.12
