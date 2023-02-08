import pathlib

import numpy as np
import torch

from ray_quickstart.init import platform

BASE_DIR = str(pathlib.Path(__file__).parents[2]).replace('\\' , '/')
CONFIG_DIR = BASE_DIR + '/config'
RUNS_DIR = BASE_DIR + '/runs'
SRC_DIR = BASE_DIR + '/src'


class Config:

    def __init__(self):
        super().__init__()

        self.seed = 1234
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)

        self.framework = 'pt' # 'pt' or 'tf'
        self.device_type = platform.get_device_type()

        self.trial_results_dir = '~/ray_results'

        self.run_on_ray_cluster = platform.is_mac()

    def get_run_on_ray_cluster(self):
        return self.run_on_ray_cluster


config = Config()
