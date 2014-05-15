
import os,glob
from setuptools import setup,find_packages

VERSION='1.0.4'
README = open(os.path.join(os.path.dirname(__file__),'README.md'),'r').read()

setup(
    name = 'jsontester',
    version = VERSION,
    license = 'PSF',
    keywords = 'Network JSON Request Test',
    url = 'http://tuohela.net/packages/jsontester',
    zip_safe = False,
    install_requires = ('requests>=1.2.3', 'nose', 'configobj'),
    scripts = glob.glob('bin/*'),
    packages = ['jsontester'] + ['jsontester.%s'%s for s in find_packages('jsontester')],
    author = 'Ilkka Tuohela',
    author_email = 'hile@iki.fi',
    description = 'Scripts to test JSON API requests from command line',
    long_description = README,
    install_requires = [ 
        'systematic>=4.0.4' 
    ],
)

