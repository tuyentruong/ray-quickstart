"""
Manager for managing directories and files for the project.
"""
import os
import shutil

from config import BASE_DIR
from log import log


class StorageManager:

    def get_config_dir(self):
        return BASE_DIR + '/config'

    def get_data_base_dir(self):
        return BASE_DIR + '/data'

    def get_data_dir(self):
        return f'{self.get_data_base_dir()}'

    def get_logs_dir(self):
        return BASE_DIR + '/logs'

    def get_models_dir(self):
        return BASE_DIR + '/models'

    def get_runs_dir(self):
        return BASE_DIR + '/runs'

    def get_src_dir(self):
        return BASE_DIR + '/src'

    def clean_for_training(self):
        self._delete_training_checkpoint_dirs()
        self._delete_training_logs_dirs()

    def _delete_training_checkpoint_dirs(self):
        if not os.path.exists(self.get_runs_dir()):
            return
        for dir_name in os.listdir(self.get_runs_dir()):
            if dir_name.startswith('checkpoint-'):
                self._delete_dir(f'{self.get_runs_dir()}/{dir_name}')

    def _delete_training_logs_dirs(self):
        if not os.path.exists(self.get_logs_dir()):
            return
        for filename in os.listdir(self.get_logs_dir()):
            if os.path.isdir(f'{self.get_logs_dir()}/{filename}'):
                self._delete_dir(f'{self.get_logs_dir()}/{filename}')
            if filename.startswith('events.out'):
                os.remove(f'{self.get_logs_dir()}/{filename}')

    def _delete_dir(self, dir_path):
        if not os.path.exists(dir_path):
            return
        log.info(f'deleting {dir_path}...')
        try:
            shutil.rmtree(dir_path)
        except OSError:
            os.remove(dir_path)

    def copy_file(self, filename, src_dir, dst_dir):
        log.info(f'copying {src_dir} to {dst_dir}')
        if os.path.exists(f'{dst_dir}/{filename}'):
            os.remove(f'{dst_dir}/{filename}')
        shutil.copy(f'{src_dir}/{filename}', dst_dir)
