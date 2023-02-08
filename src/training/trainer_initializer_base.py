"""
Base class for trainer initializers
"""
from abc import ABC, abstractmethod

import ray

from data.dataset_util import split_dataset_for_classification


class TrainerInitializerBase(ABC):

    def __init__(self, storage_manager, model, config):
        super().__init__()
        self.storage_manager = storage_manager
        self.model = model
        self.model_name = model.model_name
        self.config = config

    @abstractmethod
    def model_init(self):
        raise NotImplementedError('need to implement model_init()')

    def get_train_and_eval_datasets(self, model):
        dataset = self.dataset_init(model, is_eval=False)
        train_dataset, eval_dataset = split_dataset_for_classification(dataset, 0.9) # not using a validation dataset right now because our dataset is too small for classes
        return train_dataset, eval_dataset

    def dataset_init(self, model, is_eval=False):
        return self.do_dataset_init(model, is_eval=is_eval)

    @abstractmethod
    def do_dataset_init(self, model, is_eval=False):
        raise NotImplementedError('need to implement do_dataset_init()')

    def convert_to_ray_dataset(self, dataset):
        return ray.data.from_items(dataset)

    @abstractmethod
    def trainer_args_init(self, model):
        raise NotImplementedError('need to implement trainer_args_init()')

    def preprocessor_init(self, model):
        return None

    @abstractmethod
    def data_collator_init(self, model):
        raise NotImplementedError('need to implement data_collator_init()')

    def compute_metrics_init(self):
        return None

    def compute_objective_init(self):
        return None

    @abstractmethod
    def trainer_init(self, model, args, train_dataset, eval_dataset, scaling_config):
        raise NotImplementedError('need to implement trainer_init()')

    @abstractmethod
    def trainer_init_per_worker(self, train_dataset, eval_dataset, **trainer_init_config):
        raise NotImplementedError('need to implement trainer_init_per_worker()')

    @abstractmethod
    def update_model_with_best_checkpoint(self, model, checkpoints, default_eval_metric):
        raise NotImplementedError('need to implement trainer_init()')
