from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='share_drive',
    version='1.0.0',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'share-drive-client = source.share_drive_client.client:main',
            'share-drive-server = source.share_drive_server.server:main',
        ],
    },
)
