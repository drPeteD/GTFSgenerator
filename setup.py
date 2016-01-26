#!/usr/bin/env python

from distutils.core import setup

setup(
        name='gtfsgenerator',
        version='0.9.0',
        packages=['gtfsgenerator'],
        package_dir={'': 'src'},
        url='',
        license='MIT',
        author='Dr. Pete Dailey',
        author_email='daileypj@gmail.com',
        description='Generate GTFS feed files from config, Google Sheet, & KMLs'
)
