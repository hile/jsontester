
import os
import glob
from setuptools import setup, find_packages

VERSION='1.1'

setup(
    name = 'jsontester',
    version = VERSION,
    license = 'PSF',
    keywords = 'json request test browser',
    url = 'http://tuohela.net/packages/jsontester',
    author = 'Ilkka Tuohela',
    author_email = 'hile@iki.fi',
    description = 'Scripts to test JSON API requests from command line',
    scripts = glob.glob('bin/*'),
    packages = find_packages(),
    install_requires = (
        'requests>=1.2.3',
        'nose',
        'configobj',
        'systematic>=4.0.4',
    ),
)

