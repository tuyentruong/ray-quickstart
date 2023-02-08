import logging
import logging.config
import os
import pathlib


LOGS_DIR = str(pathlib.Path(__file__).parents[2]).replace('\\' , '/') + '/logs'


def setup_logging():
    if not os.path.exists(LOGS_DIR):
        os.mkdir(LOGS_DIR)
    file_filename = f'{LOGS_DIR}/ray_quickstart.log'
    file_write_mode = 'w'
    file_log_level = 'DEBUG'
    file_log_formatter = 'file'
    config_dir = str(pathlib.Path(__file__).parents[2]).replace('\\' , '/') + '/config'
    if os.path.exists(f'{config_dir}/logging.ini'):
        logging.config.fileConfig(f'{config_dir}/logging.ini',
                                  defaults={'file_filename': file_filename,
                                            'file_write_mode': file_write_mode,
                                            'file_log_level': file_log_level,
                                            'file_log_formatter': file_log_formatter},
                                  disable_existing_loggers=True)

    # Tensorflow logging
    logging.getLogger('h5py').setLevel(logging.INFO)
    logging.getLogger('tensorflow').setLevel(logging.INFO)

    # transformers logging
    logging.getLogger('transformers.configuration_utils').setLevel(logging.WARN)

    logger = logging.getLogger('app')
    logger.setLevel(logging.INFO)

    return logger


def truncate_logs():
    if os.path.exists(LOGS_DIR + '/ray_quickstart.log'):
        print('truncating log files')
        with open(f'{LOGS_DIR}/ray_quickstart.log', 'w') as f:
            f.truncate(0)


log = setup_logging()
