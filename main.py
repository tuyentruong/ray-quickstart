#!/usr/bin/env python
"""
Runs the specified pipeline for the example Ray QuickStart project using the defaults for each action.
"""
import sys

from data.storage_manager import StorageManager
from log import log
from models.gpt2 import GPT2
from training.gpt2_trainer_initializer import GPT2TrainerInitializer
from training.trainer import train, tune_hyperparameters

sys.path.insert(0, 'src')

import argparse
from enum import Enum, auto


class Action(Enum):
    TRAIN_MODEL = auto()  # train the model
    TUNE_MODEL_HYPERPARAMETERS = auto()  # tune hyperparameters for model
    GENERATE_TEXT = auto()  # generate text using the model


def train_model(storage_manager):
    log.info('training GPT2 model on Shakespeare corpus...')
    model = GPT2(storage_manager, 'shakespeare_char', 'text-generation')
    storage_manager.clean_for_training()
    train(GPT2TrainerInitializer(storage_manager, model))


def tune_model_hyperparameters(storage_manager):
    log.info('searching for best hyperparameters for GPT2 model trained on Shakespeare corpus...')
    storage_manager.clean_for_training()
    model = GPT2(storage_manager, 'gpt2', 'text-generation')
    tune_hyperparameters(GPT2TrainerInitializer(storage_manager, model))


def main(pipeline):
    storage_manager = StorageManager()

    log.info(f'running pipeline: {[action.name for action in pipeline]}')
    for action in pipeline:
        if action == Action.TRAIN_MODEL:
            train_model(storage_manager)
        if action == Action.TUNE_MODEL_HYPERPARAMETERS:
            tune_model_hyperparameters(storage_manager)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', type=str, required=False, help='action to perform')
    opt = parser.parse_args()

    if opt.action is not None:
        pipeline = [Action[opt.action]]
    else:
        # DIRECTION: change this to modify the action taken
        pipeline = [Action.TRAIN_MODEL]

    main(pipeline)
