"""
Utilities for working with Ray.
"""
import os
import shutil
import subprocess

import ray
import yaml
from ray import logger

from ray_quickstart.monkey_patch import monkey_patch_base_trainer_to_enable_syncing_after_training, \
    monkey_patch_trainable_util_to_fix_checkpoint_paths
from ray_quickstart.rsync_syncer import RsyncSyncer
from ray_quickstart.util import platform
from ray_quickstart.util.platform import expand_user_home_path


def initialize_ray_with_syncer(base_dir,
                               src_dir,
                               config_file_path,
                               success_callback=None,
                               clean_trial_results_dir_at_start=True):
    if ray.is_initialized():
        return
    if not os.path.exists(config_file_path):
        raise FileNotFoundError(f'config file not found at {config_file_path}')
    with open(config_file_path, 'r') as f:
        ray_config = yaml.safe_load(f)
    driver_user = ray_config['driver']['user']
    driver_hostname_or_ip_address = ray_config['driver']['hostname_or_ip_address']
    driver_private_key_file = ray_config['driver']['private_key_file']
    worker_user = ray_config['worker']['user']
    worker_hostname_or_ip_address = ray_config['worker']['hostname_or_ip_address']
    worker_ssh_port = ray_config['worker']['ssh_port']
    worker_platform = ray_config['worker']['platform']
    syncer = RsyncSyncer(driver_user,
                         driver_hostname_or_ip_address,
                         driver_private_key_file,
                         worker_user,
                         worker_hostname_or_ip_address,
                         worker_ssh_port,
                         worker_platform)
    monkey_patch_base_trainer_to_enable_syncing_after_training()
    try:
        if clean_trial_results_dir_at_start:
            clean_trial_results_dir(syncer)
        configure_remote_ray_runtime_environment(base_dir,
                                                 driver_private_key_file,
                                                 worker_user,
                                                 worker_hostname_or_ip_address,
                                                 worker_ssh_port,
                                                 '~/git/ray-quickstart')
        initialize_ray(src_dir, ray_config, success_callback)
        return syncer
    except ConnectionError:
        if platform.is_windows():
            with subprocess.Popen(f'{base_dir}/scripts/ray_start.bat') as p:
                p.wait()
            initialize_ray(src_dir, ray_config, success_callback)
            return syncer
        else:
            raise


def initialize_ray(src_dir, props, success_callback=None):
    # runtime_env is required for cloudpickle to be able to find modules
    runtime_env = {'working_dir': src_dir}
    #ray.init(local_mode=True)
    ray_head_hostname_or_ip_address = props['ray_head']['hostname_or_ip_address']
    ray_head_client_server_port = props['ray_head']['client_server_port']
    ray.init(address=f'ray://{ray_head_hostname_or_ip_address}:{ray_head_client_server_port}', runtime_env=runtime_env)
    monkey_patch_trainable_util_to_fix_checkpoint_paths()
    if success_callback is not None:
        success_callback()


def get_local_trial_results_dir():
    return f'~/ray_results'


def clean_trial_results_dir(syncer):
    logger.info('cleaning local trial results dir...')
    local_trial_results_dir = os.path.expanduser(get_local_trial_results_dir())
    if os.path.exists(local_trial_results_dir):
        delete_dir_contents(local_trial_results_dir)
    else:
        os.makedirs(local_trial_results_dir, exist_ok=True)
    if syncer is not None:
        logger.info('cleaning ray worker trial results dir...')
        trial_results_dir = get_local_trial_results_dir()
        syncer.sync_from_driver_to_ray_worker(trial_results_dir,
                                              expand_user_home_path(trial_results_dir,
                                              syncer.worker_user,
                                              syncer.worker_platform))


def configure_remote_ray_runtime_environment(base_dir,
                                             driver_private_key_file,
                                             worker_user,
                                             worker_hostname_or_ip_address,
                                             worker_ssh_port,
                                             worker_base_dir):
    sync_cmd = f'rsync -avz -e "ssh -i {driver_private_key_file} -o StrictHostKeyChecking=no -p {worker_ssh_port}" --include="Pipfile" --include="requirements.txt" --include="configure_ray_runtime_env.sh" --exclude="*" {{{base_dir}/,{base_dir}/config/}} {worker_user}@{worker_hostname_or_ip_address}:{worker_base_dir}/'
    logger.info(f'copying runtime environment configuration files to remote Ray runtime: {sync_cmd}')
    try:
        output = str(subprocess.check_output(sync_cmd, shell=True)).replace('\\n', '\n')
        logger.info(output)
    except subprocess.CalledProcessError as e:
        logger.error(f'error copying runtime environment configuration files to remote Ray runtime: {e}')

    logger.info('configuring remote Ray runtime environment...')
    configure_cmd = f'ssh -i {driver_private_key_file} -o StrictHostKeyChecking=no -p {worker_ssh_port} {worker_user}@{worker_hostname_or_ip_address} "chmod +x {worker_base_dir}/configure_ray_runtime_env.sh && {worker_base_dir}/configure_ray_runtime_env.sh"'
    try:
        output = str(subprocess.check_output(configure_cmd, shell=True)).replace('\\n', '\n')
        logger.info(output)
    except subprocess.CalledProcessError as e:
        logger.error(f'error configuring remote Ray runtime environment: {e}')


def delete_dir_contents(dir_path):
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path, ignore_errors=True)


def sync_checkpoints_back_to_driver(syncer):
    trial_results_dir = get_local_trial_results_dir()
    syncer.sync_from_ray_worker_to_driver(expand_user_home_path(trial_results_dir,
                                                                syncer.worker_user,
                                                                syncer.worker_platform),
                                          trial_results_dir)
