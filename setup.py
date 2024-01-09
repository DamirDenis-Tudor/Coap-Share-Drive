from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='share_drive',
    version='1.0.0',
    author='Damir Denis-Tudor',
    author_email='denis-tudor.damir@student.tuiasi.ro',
    description='Share drive app based on coap protocol',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'share-drive-client = share_drive.share_drive_client.client:main',
            'share-drive-server = share_drive.share_drive_server.server:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)