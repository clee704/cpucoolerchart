#! /usr/bin/env python
import os
from setuptools.command.test import test
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from cpucoolerchart import __version__


def readme():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
            return f.read()
    except Exception:
        return ''


class pytest(test):

    def finalize_options(self):
        test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        from pytest import main
        errno = main(self.test_args)
        raise SystemExit(errno)


setup(
    name='cpucoolerchart',
    version=__version__,
    url='https://github.com/clee704/cpucoolerchart',
    license='GNU AGPL v3',
    author='Choongmin Lee',
    author_email='choongmin@me.com',
    description='CPU cooler performance and price database',
    long_description=readme(),
    packages=['cpucoolerchart'],
    install_requires=[
        'requests>=2.2.0',
        'lxml>=3.2.5',
        'prettytable>=0.7.2',
        'Flask>=0.10.1',
        'Flask-SQLAlchemy>=1.0',
        'Flask-Cache>=0.12',
        'Flask-Script>=0.6.6',
    ],
    tests_require=[
        'pytest>=2.5.1',
        'mock>=1.0.1',
        'redis>=2.9.0',
    ],
    cmdclass={'test': pytest},
    entry_points={
        'console_scripts': [
            'cpucoolerchart = cpucoolerchart.command:main',
        ],
    },
    keywords='cpu heatsink cooler performance price database',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Communications',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
)