#!/usr/bin/env python

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    install_requires = f.readlines()
install_requires = [line.strip() for line in install_requires]

setup(
    name='autovar',
    version='0.0.1a5',
    description='Experiment variables management framework.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yangarbiter/autovar/',
    author='Yao-Yuan Yang',
    author_email='yangarbiter@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
    ],
    keywords='',
    packages=find_packages(exclude=[]),
    install_requires=install_requires,
    test_suit='autovar',
    extras_require={
        'dev': ['pylint'],
        'test': ['coverage', 'pylint', 'mypy'],
    },
    package_data={},
    entry_points={},
    project_urls={},
)
