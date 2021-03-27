#!/usr/bin/env python
from setuptools import find_packages, setup

__version__ = '0.0.1'


setup(
    name='inat-backlog-slogger',
    version=__version__,
    author='Jordan Cook',
    url='https://github.com/JWCook/inat-backlog-slogger',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'aiofiles',
        'aiohttp',
        'jinja2',
        'pandas',
        'pyarrow',
        'pyinaturalist==0.13.0.dev221',
        'requests-cache==0.6.0.dev2',
        'rich',
    ],
    extras_require={
        'dev': [
            'black==20.8b1',
            'flake8',
            'isort',
            'mypy',
            'pre-commit',
        ],
    },
)
