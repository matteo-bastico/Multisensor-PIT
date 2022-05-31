from setuptools import find_packages, setup


setup(
    name='mpit',
    packages=find_packages(include=['mpit',
                                    'mpit.utils']),
    version='0.4.0',
    description='Multisensor Person Identification and Tracking (PIT)',
    author='Matteo Bastico',
    license='MIT',
    install_requires=['scipy>=1.7.2',
                      'numpy>=1.21.4',
                      'similaritymeasures>=0.4.4',
                      'matplotlib>=3.5.2',
                      'pandas>=1.4.2']
)
