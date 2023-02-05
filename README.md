This project allows you to quickly set up your machine-learning project so that you can develop locally on your computer and 
then train and tune your models remotely on a GPU-enabled computer. The remote training/tuning is implemented using 
[Ray](https://github.com/ray-project/ray).

## Why Ray QuickStart?

I think a lot of developers (like me) who are interested in getting started with ML learning are using Macs for their 
development, but Macs don't have GPUs and MPS devices are still nowhere close to being as fast as GPUS. I ended up 
buying a GPU card for my Windows computer, but found it cumbersome to develop on my Mac, commit my changes to GitHub, 
push the changes to my Windows computer, and then run my training and tuning from my Windows computer. In addition, 
I found myself having to manually save the trained models to the cloud and then download them to my Mac to use them for 
inference afterwards.

Ray was designed to address this inefficiency, but I didn't find it as easy as I would have liked to get it set up for 
remote training and tuning on another computer. It's possible that they have the functionality already in place, so 
please let me know if I am reinventing the wheel somewhere.

The quickstart enable three main things:
1. Sync your Python code to the remote computer.
2. Uses Ray to perform the distributed training and tuning.
3. Sync the trained model/checkpoints back to your computer.

Over time, I hope to add additional functionality to allow you to train from a cluster in the cloud once your needs 
exceed the capabilities of your GPU card.

## Limitations Addressed By Ray QuickStart

This project does the following to make it easier for you to get started with remote training and tuning:
1. Help you create an Ubuntu 22.04 VM on your Windows computer using WSL2. I need Windows for some of my work and tried
to run the Ray cluster directly from Windows, but it doesn't look like Ray supports it yet: I ran into issues trying to 
sync the checkpoints from Windows to my Mac computer.
2. Note that you will need to start the Ubuntu instanceYou will need to start your Ubuntu instance using wsl

## Setup

1. You can get started by either cloning this repository or by installing the ray-quickstart package from PyPI. The former
is preferred if you want to try out the example project, but the latter is preferred if you want to use this package in
your own project.

2. If your GPU-enabled computer has Windows installed, you can run `setup\setup_windows.bat` to set up Ubuntu 22.04 
on your computer. Some terminal windows will open during the setup process. You can close them once the setup is complete.

If your GPU-enabled computer has Ubuntu installed, you can run `setup/setup_ubuntu.sh` to set it up.

On your Mac, you will need to install grpcio using Conda and then copy it over to your pipenv's site-packages (see `setup/setup_mac.sh`).

3. After Ubuntu has been installed, you will need to add your public SSH key to ~/.ssh/authorized_keys on your Ubuntu 
instance so that your local computer will be able to connect to the Ubuntu instance for training/tuning.
## Setup
1. Create a YAML configuration file named `ray_config.yaml` in the root directory of your project.
1. Ray QuickStart expects a configuration file named `ray_config.yaml` to be present in the root directory of your project.

## Troubleshooting

**When I connect to the Ubuntu WSL instance, it says that the GPU is not available. What can I do to fix this?** 
   
I got stumped on this issue for a while. From https://github.com/microsoft/WSL/issues/9185, I discovered the cause:
   
> There is an issue when nvidia-smi doesn't work when one instance is launched as Administrator and another as a non-Administrator.

When I started the Ubuntu WSL instance from the command line and passed in the `--user` flag with the same username as 
in Windows, then it worked. It is recommended that you start the Ubuntu WSL instance using the `ubuntu_start.sh` script.

**I am getting ModuleNotFoundError: No module named '[module]' when I try to training remotely. How do I fix it?**

You will need to install all your package dependencies to the ray-quickstart project because that is the project used 
when starting the Ray cluster. Without those packages installed, Ray will fail when trying to export your code to the
remote machine for training.
