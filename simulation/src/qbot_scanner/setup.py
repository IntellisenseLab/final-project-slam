import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'qbot_scanner'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.urdf')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.world')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')), # Add this line!
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='netrunner',
    maintainer_email='dinethsankalpaofficial@gmail.com',
    description='Qbot 3D scanning simulation',
    license='Apache License 2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            # Added quotes and fixed typo here
            'scan_logic = qbot_scanner.scan_logic:main' 
        ],
    },
)