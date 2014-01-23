"""
    cpucoolerchart.app
    ~~~~~~~~~~~~~~~~~~

    This module creates the WSGI application object.

"""

import os

from flask import Flask

from .extensions import db, cache
from .views import views


CWD = os.path.abspath(os.getcwd())
INSTANCE_PATH = os.path.join(CWD, 'instance')

DEFAULT_CONFIG = dict(
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(INSTANCE_PATH,
                                                        'development.db'),
    CACHE_TYPE='filesystem',
    CACHE_DIR=os.path.join(INSTANCE_PATH, 'cache'),
    CACHE_DEFAULT_TIMEOUT=3600 * 3,
    CACHE_KEY_PREFIX='cpucoolerchart:',
    ACCESS_CONTROL_ALLOW_ORIGIN='*',
    UPDATE_INTERVAL=86400,
    HEROKU_API_KEY=None,
    HEROKU_APP_NAME=None,
    DANAWA_API_KEY_SEARCH=None,
    DANAWA_API_KEY_PRODUCT_INFO=None,
)


def create_app(config=None):
    """Returns a :class:`flask.app.Flask` app. Configuration is done in the
    following order:

    - `cpucoolerchart.app.DEFAULT_CONFIG`
    - *CPUCOOLERCHART_SETTINGS* envvar, if exists
    - *config* argument

    """
    app = Flask(__name__, instance_path=CWD, instance_relative_config=True)

    app.config.update(DEFAULT_CONFIG)
    if os.environ.get('CPUCOOLERCHART_SETTINGS'):
        app.config.from_envvar('CPUCOOLERCHART_SETTINGS')
    if config is not None:
        app.config.update(config)

    db.init_app(app)
    cache.init_app(app)
    app.register_blueprint(views)

    return app
