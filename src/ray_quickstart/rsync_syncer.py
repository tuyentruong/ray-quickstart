import shutil
import subprocess
import sys
import time
from typing import Optional, List

from ray import logger
from ray.tune.syncer import Syncer, DEFAULT_SYNC_PERIOD

from util.platform import expand_user_home_path


class RsyncSyncer(Syncer):

    def __init__(self,
                 driver_user,
                 driver_hostname,
                 driver_ssh_port,
                 worker_user,
                 worker_hostname,
                 worker_ssh_port,
                 worker_platform,
                 use_sync_period=False,
                 sync_at_train_end_only=True,
                 sync_period=DEFAULT_SYNC_PERIOD):
        super().__init__(sync_period)
        self.driver_user = driver_user
        self.driver_hostname = driver_hostname
        self.driver_ssh_port = driver_ssh_port
        self.driver_platform = sys.platform
        self.worker_user = worker_user
        self.worker_hostname = worker_hostname
        self.worker_ssh_port = worker_ssh_port
        self.worker_platform = worker_platform
        self.use_sync_period = use_sync_period
        self.sync_at_train_end_only = sync_at_train_end_only
        self.training_has_ended = False
        self.is_syncing = False

    def sync_up(self, local_dir: str, remote_dir: str, exclude: Optional[List] = None) -> bool:
        """Synchronize the local directory (Ray worker) to the remote directory (driver)."""
        try:
            if self.sync_at_train_end_only and not self.training_has_ended:
                return False
            if self.is_syncing:
                return False
            self.is_syncing = True
            if remote_dir.startswith('file://'):
                remote_dir = remote_dir[7:]
            remote_dir = expand_user_home_path(remote_dir, self.driver_user, self.driver_platform)
            sync_cmd = f'rsync -avz -e "ssh -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no" -p {self.driver_ssh_port} {local_dir}/ {self.driver_user}@{self.driver_hostname}:{remote_dir}/'
            logger.info(f'syncing from ray worker to local computer: {sync_cmd}')
            try:
                output = str(subprocess.check_output(sync_cmd, shell=True)).replace('\\n', '\n')
                logger.debug(output)
                self.last_sync_up_time = time.time()
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f'error syncing up: {e}')
                return False
        finally:
            self.is_syncing = False

    def sync_down(self, remote_dir: str, local_dir: str, exclude: Optional[List] = None) -> bool:
        """Synchronize the remote directory (driver) to the local directory (Ray worker)."""
        try:
            if self.is_syncing:
                return False
            self.is_syncing = True
            if remote_dir.startswith('file://'):
                remote_dir = remote_dir[7:]
            remote_dir = expand_user_home_path(remote_dir, self.driver_user, self.driver_platform)
            sync_cmd = f'rsync -avz -e "ssh -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no" --delete --ignore-errors -p {self.worker_ssh_port} {remote_dir}/ {self.worker_user}@{self.worker_hostname}:{local_dir}/'
            logger.info(f'syncing from local computer to ray worker: {sync_cmd}')
            try:
                output = str(subprocess.check_output(sync_cmd, shell=True)).replace('\\n', '\n')
                #logger.debug(output)
                self.last_sync_down_time = time.time()
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f'error syncing down: {e}')
                return False
        finally:
            self.is_syncing = False

    def sync_up_if_needed(self, local_dir: str, remote_dir: str, exclude: Optional[List] = None):
        if self.use_sync_period:
            return super().sync_up_if_needed(local_dir, remote_dir, exclude)
        elif self.training_has_ended:
            return super().sync_up(local_dir, remote_dir, exclude)
        return False

    def sync_down_if_needed(self, remote_dir: str, local_dir: str, exclude: Optional[List]           = None):
        if self.use_sync_period:
            return super().sync_down_if_needed(remote_dir, local_dir, exclude)
        return False

    def delete(self, local_dir: str) -> bool:
        if self.training_has_ended:
            return False
        if self.is_syncing:
            logger.warn(f'last sync still in progress, skipping deletion of {local_dir}')
            return False
        if local_dir.startswith('file://'):
            local_dir = local_dir[7:]
        worker_dir = expand_user_home_path(local_dir, self.worker_user, self.worker_platform)
        logger.info(f'deleting {worker_dir}')
        shutil.rmtree(worker_dir)
        return True
