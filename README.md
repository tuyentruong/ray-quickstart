Ray QuickStart allows you to quickly get started with remote training and tuning of your machine-learning
project using Ray. You can develop locally using your computer and then train and tune your models remotely on a
GPU-enabled computer. The remote training/tuning is implemented using the [Ray](https://github.com/ray-project/ray) library.


## Why Ray QuickStart?

I recently got a GPU card for my Windows computer to allow me to train my ML models more quickly. I wanted to continue
developing from my Mac computer, but the process of copying my code and data to my Windows computer, training my models, 
and then copying the trained models back to my Mac computer was cumbersome. 

I found the Ray library and decided to use it to train my models remotely on my Windows computer after developing it 
locally on my Mac computer. I ran into some issues getting started with Ray, however, so I created this project to make 
it easier for others to get started.

Ray Quickstart is available as both a [PyPI package](https://pypi.org/project/ray-quickstart/) and as a 
[GitHub repo](https://github.com/tuyentruong/ray-quickstart). You should install the PyPI package if you want to add 
remote training and tuning to your own ML project. The GitHub repo includes an example project that you can run to see 
the Ray QuickStart library in action.


## What Does Ray QuickStart Do?

Ray QuickStart will:
1. Install the packages in your project's Pipfile on your remote computer without needing to set up an auto-scaling Ray cluster.
2. Clean up your trials directories before training/tuning starts (optional).
3. Use Ray to sync your Python project code to your remote computer and train/tune your model there.
4. Sync the checkpoints from your training/tuning back to your computer.

## Setting Up Your GPU-Enabled Computer

My setup is as follows:
1. I have a Mac computer that I use for development.
2. I have a Windows 11 computer with a GPU card installed that I want to use for trainging/tuning.

I decided to set up my Ray cluster on an Ubuntu instance on my Windows computer using WSL2. I originally tried to
set up a Ray cluster on my Windows computer, but I ran into some path issues while trying to sync the checkpoints. 

To set up Ubuntu on your Windows computer, you can run `setup\setup_windows.bat` found in GitHub repo. This will create 
an Ubuntu 22.04 instance on your Windows computer and configure it with a Ray cluster. It will also open up the SSH port 
and the ports used by Ray in your Windows firewall. A terminal window will open during the setup process. You can ignore 
any errors that the window shows and close it once setup has completed.

Once the Ubuntu instance has been set up, you will need to start it. It is recommended that you start the Ubuntu instance
using the `scripts\ubuntu_start.bat` script. The script will ensure that port forwarding has been set up correctly so
that you will be able to communicate with the Ray cluster on the Ubuntu instance from your local computer.

Finally, you will need to add your public SSH key to ~/.ssh/authorized_keys on your Ubuntu instance so that your local
computer will be able to connect to the Ubuntu instance to configure your runtime environment and sync the checkpoints
using rsync.

If your GPU-enabled computer has Linux installed, you can take a look at `setup\setup_ubuntu.sh` for the setup that needs
to be done to install and configure Ray cluster. The setup script was written for Ubuntu, but hopefully it will be easy 
to adapt for other distros.


## Setting Up Your Local Computer

1. Create a YAML configuration file named `ray_config.yaml` in your project. The file should contain the following
   information:

```yaml
driver:
  user: 'tuyen' # Your username on your local computer
  private_key_file: '~/.ssh/id_rsa' # The private key file that will be used to connect to the remote computer

ray_head:
  hostname_or_ip_address: '192.168.2.4' # The hostname or IP address of the remote computer
  client_server_port: 10001 # The port that will be used to communicate with the Ray cluster

worker:
  user: 'tuyen' # The user that will be used to connect to the remote computer using SSH
  hostname_or_ip_address: '192.168.2.4' # The hostname or IP address of the remote computer
  ssh_port: 22 # The port that will be used to connect to the remote computer using SSH
  platform: 'linux' # The platform that the remote computer is running on (used for path conversion)
```

2. Add a call to `initialize_ray_with_syncer()` to your ML project code to initialize the connection with the Ray cluster.
   The call will return a syncer object.

3. Pass the syncer object to the `fit()` call in the subclass of `ray.train.base_trainer.BaseTrainer` that you are using 
   to train your model. The syncer object will be used to sync your checkpoints back to your local computer after training.


## Troubleshooting

**When I connect to the Ubuntu WSL instance, it says that the GPU is not available. What can I do to fix this?** 
   
I got stumped on this issue for a while. From https://github.com/microsoft/WSL/issues/9185, it seems to be user permission
issue:
   
> There is an issue when nvidia-smi doesn't work when one instance is launched as Administrator and another as a non-Administrator.

It started working when I started the Ubuntu WSL instance from the command line and passed in the `--user` flag with the same username as 
my Windows's username. It is recommended that you start the Ubuntu WSL instance using the `scripts\ubuntu_start.bat` script
to avoid this issue.


## Future Directions

1. Add support for training on a cluster in the cloud.
