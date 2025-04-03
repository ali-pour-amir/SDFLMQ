from setuptools import setup, find_packages

setup(
    name='sdflmq',
    version='0.1.0.2',
    author='Amir Ali-Pour',
    author_email='alipouramir93@gmail.com',
    description='A semi-decentralized federated learning framework for Python',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ali-pour-amir/SDFLMQ', 
    packages=find_packages(),  
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
        'License :: OSI Approved :: MIT License', 
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',

    entry_points={
        'console_scripts': [
            'mqttfc-dashboard = sdflmq.mqttfc_source.controller_dashboard:main',
            'sdflmq_coordinator = sdflmq.sdflmq_source.examples.coordinator:main',
        ],
    },
)
