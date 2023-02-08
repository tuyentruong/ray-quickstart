import torch
from torch.utils.data import random_split

from config import config


def split_dataset_random(dataset, split_ratio):
    """Split dataset into two datasets according to split ratio"""
    split_index = int(len(dataset) * split_ratio)
    return random_split(dataset,
                        [split_index, len(dataset) - split_index],
                        generator=torch.Generator().manual_seed(config.seed))


def split_dataset_for_classification(dataset, split_ratio):
    """Split dataset into two datasets according to split ratio and stratify by class"""
    examples_for_classes_in_dataset = {}
    for example in dataset:
        label = example['label']
        if label not in examples_for_classes_in_dataset:
            examples_for_classes_in_dataset[label] = []
        examples_for_classes_in_dataset[label].append(example)
    train_dataset = []
    eval_dataset = []
    for example_class in examples_for_classes_in_dataset.keys():
        examples = examples_for_classes_in_dataset[example_class]
        num_examples = len(examples)
        if num_examples == 0:
            continue
        elif num_examples == 1:
            train_dataset.append(examples[0])
        elif num_examples == 2:
            train_dataset.append(examples[0])
            eval_dataset.append(examples[1])
        else:
            train_examples, test_examples = split_dataset_random(examples, split_ratio)
            train_dataset.extend(train_examples)
            eval_dataset.extend(test_examples)
    return train_dataset, eval_dataset
