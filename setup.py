from setuptools import setup, find_packages

setup(
    name='sdflmq',
    version='0.1.0',
    author='Amir Ali-Pour',
    author_email='alipouramir93@gmail.com',
    description='A semi-decentralized federated learning framework for Python',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ali-pour-amir/SDFLMQ',  # Optional
    packages=find_packages(),  # Automatically finds packages like fl_lib, fl_lib.utils etc.
    include_package_data=True,
    package_data={
        "sdflmq.mqttfc_source.modules": ["metadata/*.json"],
    },
    install_requires=[
        'torch',
        'psutil',
        'numpy',
        'paho-mqtt'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # or your license
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',

    entry_points={
        'console_scripts': [
            'mqttfc-dashboard = sdflmq.mqttfc_source.controller_dashboard:main',
        ],
    },
)
