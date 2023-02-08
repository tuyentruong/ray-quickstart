"""
Trainer initializer for the GPT model.
"""
import ray
from transformers import DefaultDataCollator

from config import config
from data.gpt2_dataset import GPT2Dataset
from models.gpt2 import GPT2
from ray_quickstart.monkey_patch import monkey_patch_huggingface_utils_to_process_datasets_for_gpt2
from training.huggingface_trainer_initializer_base import HuggingFaceTrainerInitializerBase


class GPT2TrainerInitializer(HuggingFaceTrainerInitializerBase):

    def __init__(self, storage_manager, model):
        super().__init__(storage_manager, model, config)

    def get_pipeline_name(self):
        if self.model is not None:
            return self.model.pipeline_name
        else:
            return 'text-generation'

    def model_init(self):
        model = GPT2(self.storage_manager, self.model_name, self.get_pipeline_name(), False, False)
        model.load_or_create_model()
        model.set_train_mode()
        return model

    def get_train_and_eval_datasets(self, model):
        train_dataset = self.dataset_init(model, is_eval=False)
        eval_dataset = self.dataset_init(model, is_eval=True)
        return train_dataset, eval_dataset

    def do_dataset_init(self, model, is_eval=False):
        return GPT2Dataset(model, is_eval=is_eval)

    def convert_to_ray_dataset(self, dataset):
        return ray.data.from_numpy(dataset.get_data_for_ray_dataset())

    def data_collator_init(self, model):
        return DefaultDataCollator()

    def trainer_init_per_worker(self, train_dataset, eval_dataset, **trainer_init_config):
        monkey_patch_huggingface_utils_to_process_datasets_for_gpt2()
        return super().trainer_init_per_worker(train_dataset, eval_dataset, **trainer_init_config)
