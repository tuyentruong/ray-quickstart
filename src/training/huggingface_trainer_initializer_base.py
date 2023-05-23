from abc import ABC
import logging
import os

import numpy as np
from ray.air import CheckpointConfig, RunConfig
from ray.train.huggingface import HuggingFaceTrainer
from ray.train.torch import TorchConfig
from transformers import TrainingArguments
import transformers.trainer
from transformers.trainer_utils import PREFIX_CHECKPOINT_DIR

from config import RUNS_DIR
from log import log, LOGS_DIR
from ray_quickstart.util.platform import normalize_home_path_for_platform
from training.trainer_initializer_base import TrainerInitializerBase
from util import platform


class HuggingFaceTrainerInitializerBase(TrainerInitializerBase, ABC):

    def trainer_args_init(self,
                          model,
                          tensorboard_logging_strategy='epoch', # 'no', 'epoch', or 'steps'
                          save_strategy='epoch', # 'no', 'epoch', or 'steps'
                          evaluation_strategy='epoch',
                          disable_tqdm=False): # 'no', 'epoch', or 'steps'
        if self.config.get_run_on_ray_cluster():
            load_best_model_at_end = False
        else:
            load_best_model_at_end=True
        args = TrainingArguments(
            seed=self.config.seed,
            data_seed=self.config.seed,
            remove_unused_columns=True,
            output_dir=f'{RUNS_DIR}/{model.model_name}',
            logging_dir=f'{LOGS_DIR}/tensorboard', # logging for TensorBoard
            logging_strategy=tensorboard_logging_strategy,
            evaluation_strategy=evaluation_strategy,
            save_strategy=save_strategy,
            load_best_model_at_end=load_best_model_at_end,
            optim='adamw_torch',
            use_mps_device=platform.is_mac() and not self.config.get_run_on_ray_cluster() and self.config.device_type == 'mps',
            disable_tqdm=disable_tqdm,
        )
        training_args = model.load_training_args()
        if training_args is not None:
            for key, value in training_args.items():
                setattr(args, key, value)
        return args

    def trainer_init(self, model, args, train_dataset, eval_dataset, scaling_config):
        data_collator = self.data_collator_init(model)
        trainer = HuggingFaceTrainer(
            trainer_init_per_worker=self.trainer_init_per_worker,
            scaling_config=scaling_config,
            datasets={'train': train_dataset, 'evaluation': eval_dataset},
            trainer_init_config={'model': model,
                                 'args': args,
                                 'data_collator': data_collator,
                                 'compute_metrics': self.compute_metrics_init()},
            torch_config=TorchConfig(backend='gloo'),
            run_config=RunConfig(name=model.model_name,
                                 checkpoint_config=CheckpointConfig(num_to_keep=None),
                                 log_to_file=f'{model.model_name}.log')
        )
        return trainer

    def trainer_init_per_worker(self, train_dataset, eval_dataset, **trainer_init_config):
        logging.basicConfig(level=logging.INFO)
        model = 'model' in trainer_init_config and trainer_init_config['model'] or None
        model_init = 'model_init' in trainer_init_config and trainer_init_config['model_init'] or None
        args = trainer_init_config['args']
        # reinitialize the training arguments so that it gets initialized correctly on the worker
        output_dir = normalize_home_path_for_platform(args.output_dir, None, None)
        args = TrainingArguments(
            seed=args.seed,
            data_seed=args.seed,
            remove_unused_columns=args.remove_unused_columns,
            output_dir=output_dir,
            overwrite_output_dir=args.overwrite_output_dir,
            learning_rate=args.learning_rate,
            per_device_train_batch_size=args.per_device_train_batch_size,
            per_device_eval_batch_size=args.per_device_eval_batch_size,
            num_train_epochs=args.num_train_epochs,
            weight_decay=args.weight_decay,
            logging_dir=normalize_home_path_for_platform(args.logging_dir, None, None), # logging for TensorBoard
            logging_strategy=args.logging_strategy,
            evaluation_strategy=args.evaluation_strategy,
            save_strategy=args.save_strategy,
            load_best_model_at_end=args.load_best_model_at_end,
            metric_for_best_model=args.metric_for_best_model,
            optim=args.optim,
            #max_steps=1,
            no_cuda=self.config.force_cpu,
            use_mps_device=args.use_mps_device,
            disable_tqdm=args.disable_tqdm,
        )
        data_collator = trainer_init_config['data_collator']
        compute_metrics = 'compute_metrics' in trainer_init_config and trainer_init_config['compute_metrics'] or None
        trainer = Trainer(
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            model=model,
            model_init=model_init,
            args=args,
            data_collator=data_collator,
            compute_metrics=compute_metrics
        )
        return trainer

    def update_model_with_best_checkpoint(self, model, checkpoints, default_eval_metric):
        if checkpoints is None or len(checkpoints) == 0:
            return
        best_checkpoint_index = None
        best_checkpoint_value = None
        training_args = model.load_training_args()
        if training_args is not None and 'metric_for_best_model' in training_args:
            eval_metric = training_args['metric_for_best_model']
        else:
            eval_metric = default_eval_metric
        for index, checkpoint_info in enumerate(checkpoints):
            checkpoint_metrics = checkpoint_info[1]
            metric_value = checkpoint_metrics[eval_metric]
            if best_checkpoint_value is None or metric_value > best_checkpoint_value:
                best_checkpoint_value = metric_value
                best_checkpoint_index = index
        best_checkpoint = checkpoints[best_checkpoint_index][0]
        best_checkpoint_metrics = checkpoints[best_checkpoint_index][1]
        log.info(f'Best checkpoint metrics: {best_checkpoint_metrics}')
        log.info(f'Best checkpoint {eval_metric}: {best_checkpoint_value}')

        if best_checkpoint:
            with best_checkpoint.as_directory() as checkpoint_path:
                model.load_from_checkpoint(checkpoint_path)
                model.save_model()


class Trainer(transformers.trainer.Trainer):
    """Subclass of Trainer that saves the model as a Ray checkpoint (lines 32-33)"""

    def _save_checkpoint(self, model, trial, metrics=None):
        # Save model checkpoint
        checkpoint_folder = f"{PREFIX_CHECKPOINT_DIR}-{self.state.global_step}"

        run_dir = self._get_output_dir(trial=trial)
        output_dir = os.path.join(run_dir, checkpoint_folder)
        self.save_checkpoint_as_directory(output_dir)

        # Determine the new best metric / best model checkpoint
        if metrics is not None and self.args.metric_for_best_model is not None:
            metric_to_check = self.args.metric_for_best_model
            if not metric_to_check.startswith("eval_"):
                metric_to_check = f"eval_{metric_to_check}"
            metric_value = metrics[metric_to_check]

            operator = np.greater if self.args.greater_is_better else np.less
            if (
                    self.state.best_metric is None
                    or self.state.best_model_checkpoint is None
                    or operator(metric_value, self.state.best_metric)
            ):
                self.state.best_metric = metric_value
                self.state.best_model_checkpoint = output_dir

        # Save the Trainer state
        if self.args.should_save:
            self.state.save_to_json(os.path.join(output_dir, transformers.trainer.TRAINER_STATE_NAME))
            self._rotate_checkpoints(use_mtime=True, output_dir=run_dir)

    def save_checkpoint_as_directory(self, output_dir):
        self.model.set_models_dir(output_dir)
        self.model.save_model()
        self.model.set_models_dir(None)
