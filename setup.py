#!/usr/bin/env python
import ast
import os
import re

from setuptools import Command, setup


BASE_DIR = os.path.dirname(os.path.realpath(__file__))


class DependencyInstallCommand(Command):
    """Performs a clean installation of package dependencies using Pipenv."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system('pipenv --rm')
        os.system('pipenv --clear')
        os.system('pipenv install --skip-lock')
        os.system('pipenv install torch torchvision --skip-lock')
        os.system('pipenv lock')


class IncrementVersionCommand(Command):
    """Increment the version number for the package."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        version_file_path = f'{BASE_DIR}/src/ray_quickstart/__init__.py'
        with open(version_file_path, 'rb') as f:
            version_re = re.compile(r'__version__\s+=\s+(.*)')
            content = f.read().decode('utf-8')
            original_version = str(ast.literal_eval(version_re.search(content).group(1)))
            major, minor, patch = original_version.split('.')
            patch = str(int(patch) + 1)
            version = '.'.join([major, minor, patch])
            print(f'incremented version to {version}')
            content = content.replace(original_version, version)
            self.distribution.metadata.version = version
        with open(version_file_path, 'w') as f:
            f.write(content)


class PublishCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system(f'twine upload {BASE_DIR}/dist/*')


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system(f'rm -vrf {BASE_DIR}/build {BASE_DIR}/dist {BASE_DIR}/src/*.egg-info')


class ReleaseCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.run_command('clean')
        self.run_command('increment_version')
        self.run_command('sdist')
        self.run_command('bdist_wheel')
        self.run_command('publish')
        self.run_command('clean-after')


if __name__ == "__main__":
    setup(
        cmdclass={
            'dep': DependencyInstallCommand,
            'clean': CleanCommand,
            'increment_version': IncrementVersionCommand,
            'publish': PublishCommand,
            'clean-after': CleanCommand,

            'release': ReleaseCommand,
        }
    )
