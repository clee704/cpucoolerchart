#! /usr/bin/env python
import os
import sys
from setuptools.command.test import test
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from cpucoolerchart import __version__


PY2 = sys.version_info[0] == 2
PY26 = sys.version_info < (2, 7)


install_requires = [
    'lxml == 3.3.0',
    'prettytable == 0.7.2',
    'Flask == 0.10.1',
    'Flask-SQLAlchemy == 1.0',
    'Flask-Cache == 0.12' if PY2 else 'Flask-Cache-Latest == 0.12',
    'Flask-Script == 0.6.6',
    'redis == 2.9.0',
    'rq == 0.3.13',

    # Used by rq; latest version is required to support Python 3.3.
    'python-dateutil == 2.2',
]

if PY26:
    install_requires.append('ordereddict == 1.1')
    install_requires.append('importlib == 1.0.3')  # required by rq


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


# Hack to prevent stupid TypeError: 'NoneType' object is not callable error on
# exit of python setup.py test # in multiprocessing/util.py _exit_function when
# running python setup.py test (see
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html)
try:
    import multiprocessing
except ImportError:
    pass


setup(
    name='cpucoolerchart',
    version=__version__,
    url='https://github.com/clee704/cpucoolerchart',
    license='MIT',
    author='Choongmin Lee',
    author_email='choongmin@me.com',
    description='CPU cooler performance and price database',
    long_description=readme(),
    packages=['cpucoolerchart'],
    install_requires=install_requires,
    tests_require=[
        'pytest == 2.5.1',
        'pytest-cov == 1.6',
        'pytest-pep8 == 1.0.5',
        'mock == 1.0.1',
        'fakeredis-fix == 0.4.1',
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
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Communications',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
)
