"""
Setup / Installation script for tastypy.
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='tastypy',
    version='0.0.3',

    description=(
		'simple python datastructures that transparently persist to disk'),
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/enewe101/tastypy',

    # Author details
    author='Edward Newell',
    author_email='edward.newell@gmail.com',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, 
		# ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2'
    ],

    # What does your project relate to?
    keywords=(
		'datastructure database python persistence storage dictionary dict'),

    packages=['tastypy'],
	package_data={
		'tastypy': ['README.rst']
	},
	install_requires=['natsort', 'tblib']
)
