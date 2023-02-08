import subprocess
import sys

from ray import logger

from ray_quickstart.util.platform import expand_user_home_path


class RsyncSyncer:

    def __init__(self,
                 driver_user,
                 driver_private_key_file,
                 worker_user,
                 worker_hostname,
                 worker_ssh_port,
                 worker_platform,
                 trial_results_dir):
        self.driver_user = driver_user
        self.driver_private_key_file = driver_private_key_file
        self.driver_platform = sys.platform
        self.worker_user = worker_user
        self.worker_hostname = worker_hostname
        self.worker_ssh_port = worker_ssh_port
        self.worker_platform = worker_platform
        self.trial_results_dir = trial_results_dir

    def sync_from_driver_to_ray_worker(self):
        """Synchronize from the local computer (driver) to the Ray worker."""
        driver_dir = expand_user_home_path(self.trial_results_dir, self.driver_user, self.driver_platform)
        worker_dir = expand_user_home_path(self.trial_results_dir, self.worker_user, self.worker_platform)
        sync_cmd = f'rsync -avz -e "ssh -i {self.driver_private_key_file} -o StrictHostKeyChecking=no -p {self.worker_ssh_port}" --delete --ignore-errors {driver_dir}/ {self.worker_user}@{self.worker_hostname}:{worker_dir}/'
        logger.info(f'syncing from local computer to ray worker: {sync_cmd}')
        try:
            output = str(subprocess.check_output(sync_cmd, shell=True)).replace('\\n', '\n')
            logger.info(output)
        except subprocess.CalledProcessError as e:
            logger.error(f'error syncing down: {e}')

    def sync_from_ray_worker_to_driver(self):
        """Synchronize from the Ray worker to the local computer (driver)."""
        worker_dir = expand_user_home_path(self.trial_results_dir, self.worker_user, self.worker_platform)
        driver_dir = expand_user_home_path(self.trial_results_dir, self.driver_user, self.driver_platform)
        sync_cmd = f'rsync -avz -e "ssh -i {self.driver_private_key_file} -o StrictHostKeyChecking=no -p {self.worker_ssh_port}" --delete --ignore-errors {self.worker_user}@{self.worker_hostname}:{worker_dir}/ {driver_dir}/'
        logger.info(f'syncing from ray worker to local computer: {sync_cmd}')
        try:
            output = str(subprocess.check_output(sync_cmd, shell=True)).replace('\\n', '\n')
            logger.info(output)
        except subprocess.CalledProcessError as e:
            logger.error(f'error syncing from ray worker to local computer: {e}')
