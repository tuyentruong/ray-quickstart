"""
Convenience function for getting info about the current OS platform
"""
import os
import sys

import torch


def get_device_type():
    """returns the device type as a string"""
    #return 'cpu'
    # noinspection PyUnresolvedReferences
    if torch.cuda.is_available():
        return 'cuda'
    elif torch.backends.mps.is_available():
        return 'mps'
    else:
        return 'cpu'


def get_cuda_device_count():
    return torch.cuda.device_count()


def get_cpu_device_count():
    return os.cpu_count()


def is_linux():
    return sys.platform == 'linux' or sys.platform == 'linux2'


def is_mac():
    return sys.platform == 'darwin'


def is_windows():
    return sys.platform == 'win32'


def expand_user_home_path(path, user, platform):
    if platform == 'darwin':
        path = path.replace('~/', f'/Users/{user}/')
    elif platform == 'windows':
        path = path.replace('~/', f'C:/Users/{user}/')
    else:
        path = path.replace('~/', f'/home/{user}/')
    return path
