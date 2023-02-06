import os
import sys

import ray
from ray import logger


def monkey_patch_cloudpickle_fast():
    """This can be useful if you need to debug cloud-pickling issues"""
    from ray.cloudpickle.cloudpickle_fast import CloudPickler
    from pickle import Pickler
    import pickle

    def dump(self, obj):
        try:
            logger.info(f"DUMPING {obj}")
            return Pickler.dump(self, obj)
        except RuntimeError as e:
            if "recursion" in e.args[0]:
                msg = (
                    "Could not pickle object as excessively deep recursion "
                    "required."
                )
                raise pickle.PicklingError(msg) from e
            else:
                raise

    CloudPickler.dump = dump


def monkey_patch_base_trainer_to_enable_syncing_after_training():
    """Monkey-patch ray.train.base_trainer.BaseTrainer so we can't sync the checkpoints before retrieving the grid results so that the checkpoints are available locally."""

    from ray.train.base_trainer import BaseTrainer
    from ray.air import Result
    from ray.train.base_trainer import TrainingFailedError
    from ray.util import PublicAPI
    from ray_quickstart.init import sync_checkpoints_back_to_driver

    @PublicAPI(stability="beta")
    def fit(self, syncer=None) -> Result:
        """Runs training.

        Returns:
            A Result object containing the training result.

        Raises:
            TrainingFailedError: If any failures during the execution of
            ``self.as_trainable()``.
        """
        from ray.tune.tuner import Tuner
        from ray.tune.error import TuneError

        trainable = self.as_trainable()

        tuner = Tuner(trainable=trainable, run_config=self.run_config)
        result_grid = tuner.fit()
        assert len(result_grid) == 1
        if syncer is not None:
            sync_checkpoints_back_to_driver(syncer)
        try:
            result = result_grid[0]
            if result.error:
                raise result.error
        except TuneError as e:
            raise TrainingFailedError from e
        return result

    BaseTrainer.fit = fit


def monkey_patch_ray_dataset_for_local_training():
    """Monkey-patch ray.data.dataset.Dataset to enable local training with the Ray dataset for debugging purposes."""
    from ray.data.dataset import Dataset

    def __getitem__(self, index):
        table = ray.get(self._plan._snapshot_blocks._blocks[index])
        return {table.column_names[i]: table.columns[i][0] for i in range(len(table.columns))}

    def __len__(self):
        return self.count()

    Dataset.__len__ = __len__
    Dataset.__getitem__ = __getitem__


def monkey_patch_trainable_util_to_fix_checkpoint_paths():
    """Monkey-patch ray.tune.trainable.util.TrainableUtil to fix the checkpoint path in the home directory so the path is correct when transferred from the Ray worker to the driver"""
    from ray.tune.trainable.util import TrainableUtil

    def find_checkpoint_dir(checkpoint_path):
        """Returns the directory containing the checkpoint path.

        Raises:
            FileNotFoundError if the directory is not found.
        """
        if sys.platform == 'darwin':
            checkpoint_path = checkpoint_path.replace('/home', '/Users')
        elif sys.platform == 'win32':
            checkpoint_path = checkpoint_path.replace('/home', 'C:/Users')
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError("Path does not exist", checkpoint_path)
        if os.path.isdir(checkpoint_path):
            checkpoint_dir = checkpoint_path
        else:
            checkpoint_dir = os.path.dirname(checkpoint_path)
        while checkpoint_dir != os.path.dirname(checkpoint_dir):
            if os.path.exists(os.path.join(checkpoint_dir, ".is_checkpoint")):
                break
            checkpoint_dir = os.path.dirname(checkpoint_dir)
        else:
            raise FileNotFoundError(
                "Checkpoint directory not found for {}".format(checkpoint_path)
            )
        return os.path.normpath(checkpoint_dir)

    TrainableUtil.find_checkpoint_dir = find_checkpoint_dir
