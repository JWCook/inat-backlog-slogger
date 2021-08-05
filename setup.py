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
        'pyinaturalist~=0.14.1',
        'pyinaturalist-convert[parquet]>=0.1.0',
        'requests-cache~=0.7.2',
        'rich',
    ],
    extras_require={
        'dev': [
            'black==21.7b0',
            'flake8',
            'isort',
            'mypy',
            'pre-commit',
        ],
    },
)
