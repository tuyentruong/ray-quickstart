"""
Utilities for working with Ray.
"""
import os
import shutil
import subprocess

import ray
from ray import logger
import yaml

from ray_quickstart.monkey_patch import monkey_patch_base_trainer_to_enable_syncing_after_training, \
    monkey_patch_trainable_util_to_fix_checkpoint_paths
from ray_quickstart.rsync_syncer import RsyncSyncer
from ray_quickstart.util import platform
from ray_quickstart.util.platform import expand_user_home_path


def initialize_ray_with_syncer(base_dir,
                               src_dir,
                               ray_config_file_path,
                               trial_results_dir,
                               success_callback=None,
                               clean_trial_results_dir_at_start=True):
    """
    :param base_dir: The base directory of your project.
    :param src_dir: The base directory for your Python source code
    :param ray_config_file_path: The path to the Ray config file.
    :param trial_results_dir The directory where the Ray trial results are stored. This directory needs to have the same
           path on your local computer and at the remote computer. If the directory is in your user home directory, we
           will do the platform-dependent path expansion for you.
    :param success_callback: Callback to call when Ray is successfully initialized.
    :param clean_trial_results_dir_at_start: Whether to clean the trial results directory on your local computer and the remote computer at the start of the experiment.
    :return: an RsyncSyncer object that needs to be called after training to sync the checkpoints from the remote computer to the local computer.
    """
    ray_config = load_ray_config(ray_config_file_path)
    driver_user = ray_config['driver']['user']
    driver_private_key_file = ray_config['driver']['private_key_file']
    worker_user = ray_config['worker']['user']
    worker_hostname_or_ip_address = ray_config['worker']['hostname_or_ip_address']
    worker_ssh_port = ray_config['worker']['ssh_port']
    worker_platform = ray_config['worker']['platform']
    worker_setup_commands = ray_config['worker']['setup_commands']
    syncer = RsyncSyncer(driver_user,
                         driver_private_key_file,
                         worker_user,
                         worker_hostname_or_ip_address,
                         worker_ssh_port,
                         worker_platform,
                         trial_results_dir)
    if ray.is_initialized():
        return syncer
    monkey_patch_base_trainer_to_enable_syncing_after_training()
    try:
        if clean_trial_results_dir_at_start:
            clean_trial_results_dir(syncer, trial_results_dir)
        configure_remote_ray_runtime_environment(base_dir,
                                                 driver_private_key_file,
                                                 worker_user,
                                                 worker_hostname_or_ip_address,
                                                 worker_ssh_port,
                                                 worker_platform,
                                                 worker_setup_commands)
        initialize_ray(src_dir, ray_config_file_path, ray_config, success_callback)
        return syncer
    except ConnectionError:
        if platform.is_windows() and os.path.exists(f'{base_dir}/scripts/ray_start.bat'):
            with subprocess.Popen(f'{base_dir}/scripts/ray_start.bat') as p:
                p.wait()
            initialize_ray(src_dir, ray_config_file_path, ray_config, success_callback)
            return syncer
        else:
            raise


def initialize_ray(src_dir, ray_config_file_path, ray_config=None, success_callback=None):
    if ray.is_initialized():
        return
    if ray_config is None:
        ray_config = load_ray_config(ray_config_file_path)
    # runtime_env is required for cloudpickle to be able to find modules
    runtime_env = {'working_dir': src_dir}
    ray_head_hostname_or_ip_address = ray_config['ray_head']['hostname_or_ip_address']
    ray_head_client_server_port = ray_config['ray_head']['client_server_port']
    ray.init(address=f'ray://{ray_head_hostname_or_ip_address}:{ray_head_client_server_port}', runtime_env=runtime_env)
    monkey_patch_trainable_util_to_fix_checkpoint_paths()
    if success_callback is not None:
        success_callback()


def load_ray_config(config_file_path):
    if not os.path.exists(config_file_path):
        raise FileNotFoundError(f'config file not found at {config_file_path}')
    with open(config_file_path, 'r') as f:
        ray_config = yaml.safe_load(f)
    return ray_config


def clean_trial_results_dir(syncer, trial_results_dir):
    logger.info('cleaning local trial results dir...')
    trial_results_dir = os.path.expanduser(trial_results_dir)
    if os.path.exists(trial_results_dir):
        delete_dir_contents(trial_results_dir)
    else:
        os.makedirs(trial_results_dir, exist_ok=True)
    if syncer is not None:
        logger.info('cleaning ray worker trial results dir...')
        syncer.sync_from_driver_to_ray_worker()


def configure_remote_ray_runtime_environment(base_dir,
                                             driver_private_key_file,
                                             worker_user,
                                             worker_hostname_or_ip_address,
                                             worker_ssh_port,
                                             worker_platform,
                                             worker_setup_commands):
    worker_base_dir = expand_user_home_path(base_dir, worker_user, worker_platform)
    sync_cmd = f'rsync -avz -e "ssh -i {driver_private_key_file} -o StrictHostKeyChecking=no -p {worker_ssh_port}" --include="Pipfile" --include="requirements.txt" --exclude="*" {base_dir}/ {worker_user}@{worker_hostname_or_ip_address}:{worker_base_dir}/'
    logger.info(f'copying runtime environment configuration files to remote Ray runtime with command "{sync_cmd}"')
    try:
        output = str(subprocess.check_output(sync_cmd, shell=True)).replace('\\n', '\n')
        logger.info(output)
    except subprocess.CalledProcessError as e:
        logger.error(f'error copying runtime environment configuration files to remote Ray runtime with command "{sync_cmd}": {e}')

    if worker_setup_commands is not None and len(worker_setup_commands) > 0:
        setup_commands = ' && '.join(worker_setup_commands)
        logger.info('configuring remote Ray runtime environment...')
        configure_cmd = f'ssh -i {driver_private_key_file} -o StrictHostKeyChecking=no -p {worker_ssh_port} {worker_user}@{worker_hostname_or_ip_address} "{setup_commands}"'
        try:
            logger.info(f'configuring remote Ray runtime environment with command "{setup_commands}"')
            output = str(subprocess.check_output(configure_cmd, shell=True)).replace('\\n', '\n')
            logger.info(output)
        except subprocess.CalledProcessError as e:
            logger.error(f'error configuring remote Ray runtime environment with command "{setup_commands}": {e}')


def delete_dir_contents(dir_path):
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path, ignore_errors=True)
