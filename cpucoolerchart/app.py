# -*- coding: UTF-8 -*-
import logging
import logging.config
import os

from flask import Flask

from .config import DefaultConfig
from .extensions import db, cache, gzip, RedisCache, CompressedRedisCache
from .views import views


__dir__ = os.path.dirname(__file__)
__logger__ = logging.getLogger(__name__)


DEFAULT_BLUEPRINTS = [views]


def create_app(config=None, blueprints=None):
  """Creates a Flask app.

  If *blueprints* is None, the default blueprints will be used.
  Currently there is only one blueprint, defined in
  :mod:`cpucoolerchart.views`.

  """
  if blueprints is None:
    blueprints = DEFAULT_BLUEPRINTS
  app = Flask(__name__)
  configure_app(app, config)
  configure_logging(app)
  configure_blueprints(app, blueprints)
  configure_extensions(app)
  return app


def configure_app(app, config=None):
  """Configures the app.

  Configuration is applied in the following order:

  1. :class:`cpucoolerchart.config.DefaultConfig`
  2. :class:`cpucoolerchart.config.CCC_ENV.Config` where
     *CCC_ENV* is an environment variable and either ``production``,
     ``development`` (default), or ``test``.
  3. If *CCC_SETTINGS* environment variable is set,
     the file it is pointing to.
  4. The *config* object given as an argument, if it is not *None*.

  """
  app.config.from_object(DefaultConfig)
  env = os.environ.get('CCC_ENV', 'development')
  __logger__.info('Environment: %s', env)
  app.config.from_object('cpucoolerchart.config.{0}.Config'.format(env))
  app.config.from_envvar('CCC_SETTINGS', silent=True)
  if config is not None:
    app.config.from_object(config)


def configure_logging(app):
  """Configures logging."""
  # This makes it sure the logger is created before configuration.
  # pylint: disable=pointless-statement
  app.logger
  # Now configure
  logging.config.dictConfig(app.config['LOGGING'])
  __logger__.info('Logging configured')


def configure_blueprints(app, blueprints):
  """Registers blueprints to the app."""
  for blueprint in blueprints:
    app.register_blueprint(blueprint)


def configure_extensions(app):
  """Initializes extensions for the app."""
  db.init_app(app)

  cache.init_app(app)
  cache.app = app   # Perhaps Flask-Cache bug
  if app.config.get('CACHE_TYPE') == 'redis':
    if app.config.get('CACHE_COMPRESSION'):
      cache.cache.__class__ = CompressedRedisCache
    else:
      cache.cache.__class__ = RedisCache

  if app.config.get('GZIP'):
    gzip.init_app(app)
