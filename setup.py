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
    version='0.0.1a0',
    description='A sample Python project',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='',
    author='Yao-Yuan Yang',
    author_email='',
    classifiers=[
        'Development Status :: 3 - Alpha',
    ],
    keywords='',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=install_requires,
    extras_require={
        'dev': ['pylint'],
        'test': ['coverage', 'pylint'],
    },
    package_data={},
    entry_points={},
    project_urls={},
)
