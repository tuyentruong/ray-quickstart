Ray QuickStart allows you to quickly get started with remote training and tuning of your machine-learning
project using Ray. You can develop locally using your computer and then train and tune your models remotely on a
GPU-enabled computer. The remote training/tuning is implemented using the [Ray](https://github.com/ray-project/ray) library.


## Why Ray QuickStart?

I recently got a GPU card for my Windows computer to allow me to train my ML models more quickly. I wanted to continue
developing from my Mac computer, but the process of copying my code and data to my Windows computer, training my models, 
and then copying the trained models back to my Mac computer was cumbersome. 

I found the Ray library and thought it could be a great solution to my problem of having to manually copy my code, data,
and models to my Windows computer for training and tuning. I ran into some issues getting started with Ray, however, so 
I created this project to make it easier for others to get started.

Ray Quickstart is available as both a [PyPI package](https://pypi.org/project/ray-quickstart/) and as a 
[GitHub repo](https://github.com/tuyentruong/ray-quickstart). You should install the PyPI package if you want to add 
remote training and tuning to your own ML project. The GitHub repo includes an example project that allows you to try 
out remote training on your computers.


## What Does Ray QuickStart Do?

Ray QuickStart will:
1. Install the packages in your project's Pipfile on your remote computer without needing to set up a Ray cluster environment first.
2. Clean up your trials directories before training/tuning starts *(optional)*.
3. Use Ray to sync your Python project code to your remote computer and train/tune your model there.
4. Sync the checkpoints from your training/tuning back to your computer, so you can use them for inference.

## Setting Up Your GPU-Enabled Computer

My setup is as follows:
1. I have a Mac computer that I use for development.
2. I have a Windows 11 computer with a GPU card installed that I want to use for trainging/tuning.

I decided to set up my Ray cluster on an Ubuntu instance on my Windows computer using WSL2. I originally tried to
set up a Ray cluster directly on my Windows computer, but I ran into some path issues while trying to sync the checkpoints. 
I don't think Ray fully supports Windows yet, so I thought setting it up on Ubuntu would be a safer bet.

To set up Ubuntu on your Windows computer, you can run the `setup\setup_windows.bat` script found in GitHub repo. The 
script will create an Ubuntu 22.04 instance on your Windows computer and configure it with a Ray cluster. It will also 
open up the SSH port and the ports used by Ray in your Windows firewall. A terminal window will open during the setup 
process. You can ignore any errors that the window shows and close it once setup has completed.

Once the Ubuntu instance has been set up, you will need to start it. It is recommended that you start the Ubuntu instance
using the `scripts\ubuntu_start.bat` script. The script will ensure that port forwarding has been set up correctly so
that you will be able to communicate with the Ray cluster on the Ubuntu instance from your local computer.

If your GPU-enabled computer has Linux installed, you can take a look at `setup\setup_ubuntu.sh` for the setup that needs
to be done to install and configure Ray cluster. The setup script was written for Ubuntu, but hopefully it will be easy 
to adapt for other distros.


## Setting Up Your Local Computer

1. Copy ~/.ssh/id_rsa_ubuntu from the Ubuntu instance to your local computer. The SSH key will be used by your local
   computer to connect to the Ubuntu instance the computer to configure your runtime environment and sync the checkpoints
   using rsync. Alternatively, you can add the public key for an existing SSH key to ~/.ssh/authorized_keys on your Ubuntu 
   instance.

2. Finally, you will need to add your public SSH key to ~/.ssh/authorized_keys on your Ubuntu instance so that your local
   computer will be able to connect to the Ubuntu instance to configure your runtime environment and sync the checkpoints
   using rsync.

3. Create a YAML configuration file named `ray_config.yaml` in your project. The file should contain the following
   information:
   
   ```yaml
   driver:
     user: 'tuyen' # Your username on your local computer
     private_key_file: '~/.ssh/id_rsa_ubuntu' # The private key file that will be used to connect to the remote computer
   
   ray_head:
     hostname_or_ip_address: '192.168.2.4' # The hostname or IP address of the remote computer
     client_server_port: 10001 # The port that will be used to communicate with the Ray cluster
   
   worker:
     user: 'tuyen' # The user that will be used to connect to the remote computer using SSH
     hostname_or_ip_address: '192.168.2.4' # The hostname or IP address of the remote computer
     ssh_port: 22 # The port that will be used to connect to the remote computer using SSH
     platform: 'linux' # The platform that the remote computer is running on (used for path conversion)
     base_dir: '~/git/ray-quickstart' # The base directory where ray was installed and the ray cluster was started on the remote computer
     setup_commands: # The commands that will be run on the remote computer to set up the runtime environment
       - source ~/anaconda3/etc/profile.d/conda.sh
       - conda activate ray-quickstart
       - pipenv install --skip-lock
   ```
   
4. Add a call to `initialize_ray_with_syncer()` to your ML project code to initialize the connection with the Ray cluster.
   The call will return a syncer object:
   
   ```
   syncer = initialize_ray_with_syncer('~/git/ray-quickstart',
                                       '~/git/ray-quickstart/src',
                                       '~/git/ray-quickstart/config/ray_config.yaml',
                                       '~/ray-results')
   ```

5. Pass the syncer object to the `fit()` call in the subclass of `ray.train.base_trainer.BaseTrainer` that you are using 
   to train your model. The syncer object will be used to sync your checkpoints back to your local computer after training:

   ```
   trainer.fit(syncer)
   ```


## Example Project

The example project in this repo is taken from Andrej Karpathy's great [nanoGPT](https://github.com/karpathy/nanoGPT) repo.
I have been looking at his repo while watching his corresponding YouTube video 
[Let's build GPT: from scratch, in code, spelled out](https://www.youtube.com/watch?v=kCc8FmEb1nY&t=5419s). His repo includes
a smaller GPT2 character-based model that you can train using text from Shakespeare. I ported the example so that I 
could try training it using my Ray QuickStart setup. I didn't port his GPT2 model over, though, but used the HuggingFace 
GPT2 model instead. The `train.bin` and `val.bin` are the pre-processed data files in binary format that were generated 
from his nanoGPT repo.

You can configure the project from `src/config/__init__.py`.

## FAQ

**Why didn't you use Ray's default syncer?**

It didn't work for me when I tried it with their `ray.train.huggingface.HuggingFaceTrainer` class. I believe their
HuggingFace trainer only supports sync'ing to cloud storage, but I wanted to have the sync'ing to occur directly between
my local and remote computer.

**Why didn't you implement a custom `ray.tune.sync.Syncer` to perform the sync'ing?**

I did that originally, but sync'ing the checkpoints back to my local computer required that the Ray worker be able to 
SSH into my local computer. I didn't want you to have to install an SSH key on the remote computer that would give the
computer SSH access to your local computer, so I reimplemented it so that your local computer connects to the remote 
computer at the end of training/tuning to retrieve the checkpoints.

**Why didn't you use Ray's cluster environment to set up your project dependencies on your Ray worker?**

I hadn't gotten around to configuring a Ray cluster yet and I wanted needed something lightweight that didn't require me 
to modify my Ray instance once I had it up and running.


## Troubleshooting

**When I connect to the Ubuntu WSL instance, it says that the GPU is not available. What can I do to fix this?** 
   
I got stumped on this issue for a while. From https://github.com/microsoft/WSL/issues/9185, it seems to be user permission
issue:
   
> There is an issue when nvidia-smi doesn't work when one instance is launched as Administrator and another as a non-Administrator.

It started working when I started the Ubuntu WSL instance from the command line and passed in the `--user` flag with the same username as 
my Windows's username. It is recommended that you start the Ubuntu WSL instance using the `scripts\ubuntu_start.bat` script
to avoid this issue.

**I get an OOM (out-of-memory) error when I try to train my model on the remote computer. How can I fix this?**

Unfortunately, the GPT2 model is really large and requires a lot of memory. If you don't have enough GPU memory, you can 
add `no_cuda=True` to the `TrainingArguments` object created in `huggingface_trainer_initializer_base.py.trainer_init_per_worker`
to try training with the CPU. You can also edit `gpt2_dataset.py` and modify the `get_num_examples()` method to return a 
small number like 100 so that you can see the complete training process.


## Future Directions

1. Add support for training on a cluster in the cloud.
