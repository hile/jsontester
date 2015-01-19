
import os,glob
from setuptools import setup, find_packages

VERSION='1.0.5'

setup(
    name = 'jsontester',
    version = VERSION,
    license = 'PSF',
    keywords = 'Network JSON Request Test',
    url = 'http://tuohela.net/packages/jsontester',
    scripts = glob.glob('bin/*'),
    packages = ['jsontester'] + ['jsontester.%s'%s for s in find_packages('jsontester')],
    author = 'Ilkka Tuohela',
    author_email = 'hile@iki.fi',
    description = 'Scripts to test JSON API requests from command line',
    install_requires = (
        'requests>=1.2.3',
        'nose',
        'configobj',
        'systematic>=4.0.4',
    ),
)

