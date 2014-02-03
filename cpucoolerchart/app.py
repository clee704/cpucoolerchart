"""
    cpucoolerchart.app
    ~~~~~~~~~~~~~~~~~~

    This module creates the WSGI application object.

"""

import os

from flask import Flask

from ._compat import string_types, iteritems
from .extensions import db, cache, redis
from .views import views


__all__ = ['DEFAULT_CONFIG', 'create_app']


CWD = os.path.abspath(os.getcwd())
INSTANCE_PATH = os.path.join(CWD, 'instance')

#: Default configuration values for the app. Note that ``{INSTANCE_PATH}`` will
#: be converted to the absolute path of ``instance`` directory under the
#: current working directiry.
DEFAULT_CONFIG = dict(
    SQLALCHEMY_DATABASE_URI='sqlite:///{INSTANCE_PATH}/development.db',
    CACHE_TYPE='filesystem',
    CACHE_DIR='{INSTANCE_PATH}/cache',
    CACHE_DEFAULT_TIMEOUT=3600 * 3,
    CACHE_KEY_PREFIX='cpucoolerchart:',
    ACCESS_CONTROL_ALLOW_ORIGIN='*',
    UPDATE_INTERVAL=86400,
    DANAWA_API_KEY_PRODUCT_INFO=None,
    DANAWA_API_KEY_SEARCH=None,
    USE_QUEUE=False,
    RQ_URL=None,
    START_WORKER_NODE=None,
    HEROKU_WORKER_NAME='worker',
    HEROKU_API_KEY=None,
    HEROKU_APP_NAME=None,
)


def iter_default_config():
    """Returns an iterator that iterates each pair of key and value from
    `DEFAULT_CONFIG`. If a value is string and contains ``{INSTANCE_PATH}``,
    it is converted according to the description of `DEFAULT_CONFIG`.

    """
    for key, value in iteritems(DEFAULT_CONFIG):
        if isinstance(value, string_types) and '{INSTANCE_PATH}' in value:
            yield key, value.format(INSTANCE_PATH=INSTANCE_PATH)
        else:
            yield key, value


def create_app(config=None):
    """Returns a CPU Cooler Chart :class:`~flask.app.Flask` app. Configuration
    is applied in the following order:

    - :data:`DEFAULT_CONFIG`
    - python file that the ``CPUCOOLERCHART_SETTINGS`` environment variable
      points to, if exists
    - *config* argument, if provided. If it is a string, the file it points to
      (relative to the current working directory or absolute) is read,
      otherwise it is assumed to be a mapping.

    For more information, see `Configuration Handling`__.

    __ http://flask.pocoo.org/docs/config/

    """
    app = Flask(__name__.split('.')[0],
                instance_path=CWD,
                instance_relative_config=True)

    app.config.update(iter_default_config())

    if os.environ.get('CPUCOOLERCHART_SETTINGS'):
        app.config.from_envvar('CPUCOOLERCHART_SETTINGS')

    if isinstance(config, string_types):
        app.config.from_pyfile(config)
    elif config is not None:
        app.config.update(config)

    db.init_app(app)
    cache.init_app(app)
    if app.config.get('USE_QUEUE'):
        redis.init_app(app)

    app.register_blueprint(views)

    return app
