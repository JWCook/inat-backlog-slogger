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
        'beautifulsoup4',
        'jinja2',
        'pyinaturalist~=0.16.0',
        'pyinaturalist-convert[parquet]~=0.2.2',
        'rich',
    ],
    extras_require={
        'dev': [
            'black',
            'flake8',
            'isort',
            'mypy',
            'pre-commit',
        ],
    },
)
