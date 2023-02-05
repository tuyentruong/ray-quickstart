#!/usr/bin/env python
import os

from setuptools import Command, setup


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system('rm -vrf ./build ./dist ./src/*.egg-info')


if __name__ == "__main__":
    setup(
        cmdclass={
            'clean': CleanCommand,
        }
    )
