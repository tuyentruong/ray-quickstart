"""
Base class for trainer implementations.
"""
import ray
from ray.air import ScalingConfig

from config import BASE_DIR, CONFIG_DIR, SRC_DIR
from data.dataset_util import split_dataset_random
from log import log
from ray_quickstart import initialize_ray, initialize_ray_with_syncer
from ray_quickstart.util.platform import get_cpu_device_count


def train(trainer_initializer):
    model = trainer_initializer.model
    model.load_or_create_model()
    model.is_training = True
    log.info(f'training {model.model_name} model...')
    train_dataset, eval_dataset = trainer_initializer.get_train_and_eval_datasets(model)
    if trainer_initializer.config.get_run_on_ray_cluster():
        syncer = initialize_ray_with_syncer(BASE_DIR,
                                            SRC_DIR,
                                            f'{CONFIG_DIR}/ray_config.yaml',
                                            trainer_initializer.config.trial_results_dir)
        log.info('training using ray cluster...')
        ray_train_dataset = trainer_initializer.convert_to_ray_dataset(train_dataset)
        ray_eval_dataset = trainer_initializer.convert_to_ray_dataset(eval_dataset)
        scaling_config = create_scaling_config()
        args = trainer_initializer.trainer_args_init(model)
        trainer = trainer_initializer.trainer_init(model,
                                                   args,
                                                   ray_train_dataset,
                                                   ray_eval_dataset,
                                                   scaling_config)
        result = trainer.fit(syncer)
        checkpoint = len(result.best_checkpoints) > 0
        if checkpoint is None:
            log.info('no best checkpoint found after training using ray cluster')
        else:
            trainer_initializer.update_model_with_best_checkpoint(model, result.best_checkpoints,
                                                                  args.metric_for_best_model)
    else:
        log.info('training using local computer...')
        model.set_train_mode()
        trainer_init_config = {
            'model': model,
            'args': trainer_initializer.trainer_args_init(model),
            'data_collator': trainer_initializer.data_collator_init(model),
            'compute_metrics': trainer_initializer.compute_metrics_init()
        }
        trainer = trainer_initializer.trainer_init_per_worker(train_dataset, eval_dataset, **trainer_init_config)
        result = trainer.train()
        log.info(f'Best checkpoint metrics: {result.metrics}')
        model = trainer.model
        model.save_model()
    log.info(f'finished training {model.model_name} model')
    return model


def tune_hyperparameters(trainer_initializer):
    initialize_ray(SRC_DIR, f'{CONFIG_DIR}/ray_config.yaml')
    model = trainer_initializer.model_init()
    evaluation_strategy = 'epoch' # 'no', 'steps', or 'epoch'
    args = trainer_initializer.trainer_args_init(model,
                                                 tensorboard_logging_strategy='no',
                                                 save_strategy='no',
                                                 evaluation_strategy=evaluation_strategy,
                                                 disable_tqdm=True)
    scaling_config = create_scaling_config()
    dataset = trainer_initializer.dataset_init(model, is_eval=False)
    train_dataset, eval_dataset = split_dataset_random(dataset, 0.9) # not using a validation dataset right now because our dataset is too small for classes
    trainer_init_config = {
        'model_init': trainer_initializer.model_init,
        'args': args,
        'data_collator': trainer_initializer.data_collator_init(model),
        'compute_metrics': trainer_initializer.compute_metrics_init()
    }
    trainer = trainer_initializer.trainer_init_per_worker(train_dataset, eval_dataset, **trainer_init_config)
    search_space = {
        'learning_rate': ray.tune.loguniform(1e-5, 1e-3),
        'per_device_train_batch_size': ray.tune.choice([4, 8, 16, 32]),
        'per_device_eval_batch_size': 32,
        'num_train_epochs': ray.tune.choice([5, 6, 7, 8, 9]),
        'weight_decay': ray.tune.loguniform(1e-3, 1e-1)
    }
    num_train_epochs_search_space = {
        'learning_rate': 6e-5,
        'per_device_train_batch_size': 32,
        'per_device_eval_batch_size': 32,
        'num_train_epochs': ray.tune.choice([20, 25, 30, 35, 40, 45, 50]),
        'weight_decay': 1e-2
    }
    from ray.tune.schedulers import ASHAScheduler
    from ray.tune.search.hyperopt import HyperOptSearch
    best_trial = trainer.hyperparameter_search(
        hp_space=lambda _:search_space,
        compute_objective=trainer_initializer.compute_objective_init(),
        n_trials=10,
        direction='maximize',
        backend='ray',
        resources_per_trial={'cpu': scaling_config.resources_per_worker['CPU'],
                             'gpu': scaling_config.resources_per_worker['GPU']},
        search_alg=HyperOptSearch(metric='objective', mode='max'),
        scheduler=ASHAScheduler(metric='objective', mode='max')
    )
    log.info(f'best trial: {best_trial}')


def create_scaling_config():
    use_gpu = True
    num_trainer_cpus = 4
    if use_gpu:
        num_cpus = 0
        num_gpus = 1
    else:
        num_cpus = get_cpu_device_count() - num_trainer_cpus - 1
        num_gpus = 0
    scaling_config = ScalingConfig(num_workers=1,
                                   use_gpu=use_gpu,
                                   trainer_resources={'CPU': num_trainer_cpus, 'GPU': 0},
                                   resources_per_worker={'CPU': num_cpus, 'GPU': num_gpus})
    return scaling_config
