"""
Dataset for use with GPT2 model.
"""
import numpy as np
from torch.utils.data import Dataset

from config import config
from log import log


class GPT2Dataset(Dataset):
    """
    This dataset is unique in that the examples are permutations of the same underlying text. It would be very inefficient
    to generate all the examples locally and then copy them over the network. Instead, we just send the underlying text and
    generate the examples on the fly from the monkey-patched RayDatasetHFIterable.
    """

    def __init__(self, model, use_memmap=False, is_eval=False):
        super().__init__()
        self.model = model
        self.dataset_name = is_eval and 'val' or 'train'
        self.block_size = model.model.config.block_size
        if use_memmap:
            self.data = np.memmap(self.get_file_path(),
                                  dtype=np.uint16,
                                  mode='r')
        else:
            self.data = np.fromfile(self.get_file_path(),
                                    dtype=np.uint16)
        log.info(f'loaded {len(self.data)} examples')

    def get_file_path(self):
        return f'{self.model.storage_manager.get_data_dir()}/{self.model.model_name}/{self.dataset_name}.bin'

    def __len__(self):
        if config.truncate_dataset_to_size is not None:
            return config.truncate_dataset_to_size
        return self.get_num_examples()

    def __getitem__(self, index):
        if index >= len(self):
            raise IndexError('index out of range')
        x = self.data[index:index+self.block_size].astype(np.int64)
        y = self.data[index+1:index+1+self.block_size].astype(np.int64)
        return {'input_ids': x, 'labels': y}

    def get_data_for_ray_dataset(self):
        # get the data as a numpy array to allow for efficient transfer to the remote workers
        return np.array([self.data[i:i+self.block_size+1] for i in range(self.get_num_examples())]) # add 1 to data length so we can create the labels later (data[x + 1:] is the label for data[x:])

    def get_num_examples(self):
        """You can edit to return a smaller number if you are running out of memory when trying to train on this dataset"""
        return len(self.data) - self.block_size
