"""
Convenience function for getting info about the current OS platform
"""
import os
import sys


def is_linux():
    return sys.platform == 'linux' or sys.platform == 'linux2'


def is_mac():
    return sys.platform == 'darwin'


def is_windows():
    return sys.platform == 'win32'


def normalize_home_path_for_platform(path, user, platform):
    if platform is None:
        platform = sys.platform
    if path.startswith('~'):
        if user is None:
            user = os.environ.get('USER')
        if platform == 'darwin':
            path = path.replace('~/', f'/Users/{user}/')
        elif platform == 'windows':
            path = path.replace('~/', f'C:/Users/{user}/')
        elif platform == 'linux':
            path = path.replace('~/', f'/home/{user}/')
    else:
        if platform == 'darwin':
            if path.startswith('/home/'):
                path = path.replace('/home/', '/Users/')
            elif path.startswith('C:/Users/'):
                path = path.replace('C:/Users/', '/Users/')
        elif platform == 'windows':
            if path.startswith('/Users/'):
                path = path.replace('/Users/', 'C:/Users/')
            elif path.startswith('/home/'):
                path = path.replace('/home/', 'C:/Users/')
        elif platform == 'linux':
            if path.startswith('/Users/'):
                path = path.replace('/Users/', '/home/')
            elif path.startswith('C:/Users/'):
                path = path.replace('C:/Users/', '/home/')
    return path
