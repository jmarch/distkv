from setuptools import setup, find_packages

setup(
    name='distkv',
    version='0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'distkv=distkv.app:main',
        ],
    },
)
