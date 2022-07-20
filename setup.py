from setuptools import setup

setup(
    name='traffic-management-system',
    version='1.0',
    packages=['elements', 'library', 'modules'],
    license='BSD 0-Clause License (0BSD)',
    license_files=('LICENSE',),
    author='',
    description='Conflict identification and management in EBD',
    install_requires=[
        'matplotlib',
        'pandas',
        'numpy',
        'pytest'
    ]
)
