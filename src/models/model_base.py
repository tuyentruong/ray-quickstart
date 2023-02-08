"""
Base for ML models
"""
from abc import abstractmethod
import os
from typing import final

import torch
from torch.nn import Module
import yaml

from config import config
from log import log


class ModelBase(Module):

    def __init__(self, model_name, storage_manager, use_trained_model, is_inference_mode=False):
        super().__init__()
        self.model_name = model_name
        self.storage_manager = storage_manager
        self.use_trained_model = use_trained_model
        self.is_inference_mode = is_inference_mode
        self.model = None
        self.is_training = False
        self.training_validation_accuracy = None
        self.models_dir_override = None # set to load model from checkpoint

    def get_device_type(self):
        return self.get_model().device

    def is_persistent_model(self):
        return True

    def set_models_dir(self, models_dir):
        self.models_dir_override = models_dir

    def get_model(self):
        if self.model is None:
            self.load_or_create_model()
        return self.model

    def get_model_path(self):
        return self._get_model_path(self.model_name)

    def _get_model_path(self, model_name):
        if self.models_dir_override is not None:
            models_dir = self.models_dir_override
        else:
            models_dir = self.storage_manager.get_models_dir()
        if self.get_save_model_in_folder():
            return f'{models_dir}/{model_name}_model'
        else:
            return f'{models_dir}/{self.get_model_framework()}_{model_name}_model'

    def get_model_framework(self):
        return config.framework == 'pt' and 'pytorch' or 'tensorflow'

    @final
    def load_or_create_model(self):
        if self.model is not None:
            return
        model_config = self.get_model_config()
        if self.is_persistent_model and self.use_trained_model:
            if os.path.exists(self.get_model_path() + (not self.get_save_model_in_folder() and '.p' or '')):
                log.info(f'loading model from {self.get_model_path()}')
                self.model = self._do_load_model(model_config)
            else:
                self.use_trained_model = False
        if self.model is None:
            log.info(f'creating {self.model_name} model')
            self.model = self._do_create_model(model_config)
        if self.is_inference_mode:
            self.to(torch.device(config.device_type))
        return self.model

    def load_from_checkpoint(self, checkpoint_dir):
        self.models_dir_override = checkpoint_dir
        model_config = self.get_model_config()
        self.model = self._do_load_model(model_config)
        self.models_dir_override = None
        self.save_model()

    def get_model_config(self):
        model_config = self._do_create_model_config()
        model_config_overrides = self.load_model_config()
        if model_config_overrides is not None:
            model_config.update(model_config_overrides)
        return model_config

    def load_model_config(self, model_config_name=None):
        model_config_file_path = self._get_model_config_file_path(model_config_name)
        if os.path.exists(model_config_file_path):
            with open(model_config_file_path, 'r') as f:
                model_config = yaml.load(f, Loader=yaml.FullLoader)
                return model_config
        return None

    def save_model_config(self, model_config, model_config_name=None):
        model_config_file_path = self._get_model_config_file_path(model_config_name)
        with open(model_config_file_path, 'w') as f:
            yaml.dump(model_config, f, default_flow_style=False)

    def _get_model_config_file_path(self, model_config_name=None):
        if model_config_name is not None:
            return f'{self.storage_manager.get_config_dir()}/{self.model_name}/model_{model_config_name}.yaml'
        else:
            return f'{self.storage_manager.get_config_dir()}/{self.model_name}/model.yaml'

    @abstractmethod
    def _do_create_model_config(self):
        raise NotImplementedError('need to implement do_create_model_config()')

    @abstractmethod
    def _do_create_model(self, model_config):
        raise NotImplementedError('need to implement do_load_model()')

    def _do_load_model(self, model_config):
        return torch.load(self.get_model_path(), map_location=torch.device(config.device_type))

    def get_save_model_in_folder(self):
        """whether the model is saved in a folder or in a single file"""
        return False

    def save_model(self):
        if self.is_persistent_model():
            self.model.save(self.get_model_path())

    def to(self, device_type):
        if self.get_device_type() != device_type:
            log.info(f'converting {self.model_name} model to device {device_type}')
            self.model.to(device_type)
        return self

    def load_training_params(self, train_params_name=None):
        training_params_file_path = self._get_train_params_file_path(train_params_name)
        if os.path.exists(training_params_file_path):
            with open(training_params_file_path, 'r') as f:
                training_params = yaml.load(f, Loader=yaml.FullLoader)
                return training_params
        return None

    def save_training_params(self, training_params, train_params_name=None):
        training_params_file_path = self._get_train_params_file_path(train_params_name)
        with open(training_params_file_path, 'w') as f:
            yaml.dump(training_params, f, default_flow_style=False)

    def _get_train_params_file_path(self, training_params_name=None):
        if training_params_name is not None:
            return f'{self.storage_manager.get_config_dir()}/{self.model_name}/train_{training_params_name}.yaml'
        else:
            return f'{self.storage_manager.get_config_dir()}/{self.model_name}/train.yaml'

    def set_train_mode(self):
        self.get_model().train()

    @abstractmethod
    def forward(self, *args, **kwargs):
        raise NotImplementedError('need to implement forward()')

    @final
    def train_model(self):
        if self.use_trained_model:
            log.info('not training because use_trained_model is set to True')
            return
        log.info(f'training {self.model_name} model...')
        self.load_or_create_model()
        self.set_train_mode()
        self.is_training = True
        self._do_train_model()
        self.save_model()
        log.info(f'finished training {self.model_name} model')

    @abstractmethod
    def _do_train_model(self):
        raise NotImplementedError('need to implement do_train_model()')

    def get_training_validation_accuracy(self):
        return self.training_validation_accuracy

    @final
    def update_model(self, message_ids):
        if self.is_persistent_model() and not self.use_trained_model:
            log.info('not updating because use_trained_model is set to False: you might want to call train() instead')
            return
        if self.is_persistent_model():
            log.info(f'updating {self.model_name} model...')
        self.load_or_create_model()
        self.is_training = True
        self._do_update_model(message_ids)
        self.save_model()
        if self.is_persistent_model():
            log.info(f'finished updating {self.model_name} model')

    @abstractmethod
    def _do_update_model(self, message_ids):
        raise NotImplementedError('need to implement do_update_model()')

    def set_eval_mode(self):
        self.get_model().eval()

    @abstractmethod
    def predict(self, *args, **kwargs):
        raise NotImplementedError('need to implement predict()')

    @abstractmethod
    def predict_batch(self, *args, **kwargs):
        raise NotImplementedError('need to implement predict_batch()')
