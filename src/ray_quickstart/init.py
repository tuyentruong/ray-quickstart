"""
Utilities for working with Ray.
"""
import os
import shutil
import subprocess

import ray
import yaml
from ray import logger
from ray_quickstart.rsync_syncer import RsyncSyncer
from ray_quickstart.util import platform
from ray_quickstart.util.platform import expand_user_home_path


def initialize_ray_with_syncer(base_dir, src_dir, config_file_path, success_callback=None):
    if ray.is_initialized():
        return
    if not os.path.exists(config_file_path):
        raise FileNotFoundError(f'config file not found at {config_file_path}')
    with open(config_file_path, 'r') as f:
        props = yaml.safe_load(f)
    driver_user = props['driver']['user']
    driver_hostname_or_ip_address = props['driver']['hostname_or_ip_address']
    driver_ssh_port = props['driver']['ssh_port']
    worker_user = props['worker']['user']
    worker_hostname_or_ip_address = props['worker']['hostname_or_ip_address']
    worker_ssh_port = props['worker']['ssh_port']
    syncer = RsyncSyncer(driver_user,
                         driver_hostname_or_ip_address,
                         driver_ssh_port,
                         worker_user,
                         worker_hostname_or_ip_address,
                         worker_ssh_port,
                         'linux')
    try:
        clear_local_trial_results_dir(syncer)
        _do_initialize_ray(src_dir, props, success_callback)
        return syncer
    except ConnectionError:
        if platform.is_windows():
            with subprocess.Popen(f'{base_dir}/scripts/ray_start.bat') as p:
                p.wait()
            _do_initialize_ray(src_dir, props, success_callback)
            return syncer
        else:
            raise


def _do_initialize_ray(src_dir, props, success_callback=None):
    # runtime_env is required for cloudpickle to be able to find modules
    runtime_env = {'working_dir': src_dir}
    #ray.init(local_mode=True)
    ray_head_hostname_or_ip_address = props['ray_head']['head_hostname_or_ip_address']
    ray_head_client_server_port = props['ray_head']['client_server_port']
    ray.init(address=f'ray://{ray_head_hostname_or_ip_address}:{ray_head_client_server_port}', runtime_env=runtime_env)
    if success_callback is not None:
        success_callback()



def get_local_trial_results_dir():
    return f'~/ray_results'


def clear_local_trial_results_dir(syncer):
    logger.info('clearing local trial results dir...')
    local_trial_results_dir = os.path.expanduser(get_local_trial_results_dir())
    if os.path.exists(local_trial_results_dir):
        delete_dir_contents(local_trial_results_dir)
    else:
        os.makedirs(local_trial_results_dir, exist_ok=True)
    if syncer is not None:
        trial_results_dir = get_local_trial_results_dir()
        syncer.sync_down(trial_results_dir,
                         expand_user_home_path(trial_results_dir,
                                               syncer.worker_user,
                                               syncer.worker_platform))


def delete_dir_contents(dir_path):
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path, ignore_errors=True)
