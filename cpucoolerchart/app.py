import logging
import logging.config
import os
import re

from flask import Flask, request, redirect
from flask.ext.assets import Bundle

from .config import DefaultConfig
from .extensions import db, cache, assets_env, gzip, redis_connection
from .rediscache import RedisCache, CompressedRedisCache
from .views import views


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
  configure_blueprints(app, blueprints)
  configure_extensions(app)
  configure_logging(app)
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

  assets_env.init_app(app)
  if app.config.get('ASSETS_DEBUG'):
    assets_env.register('js_vendor',
      'bower_components/jquery/jquery.js',
      'bower_components/angular/angular.js',
      'bower_components/fastclick/lib/fastclick.js',
      filters='yui_js', output='compiled/%(version)s.vendor.js'
    )
  assets_env.register('js_all',
    'main.js',
    filters='yui_js', output='compiled/%(version)s.script.js'
  )
  assets_env.register('css_all',
    Bundle('main.css.less', filters='less', output='compiled/%(version)s.main.css'),
    filters='yui_css', output='compiled/%(version)s.styles.css'
  )

  if app.config.get('LIVE_RELOAD'):
    # LiveReload hack
    # See https://github.com/miracle2k/webassets/issues/199
    def get_bundle_from_output(path, env_or_bundles):
      for bundle in env_or_bundles:
        output = getattr(bundle, 'output', None)
        if output == path:
          return bundle
        elif output and '%(version)s' in output:
          pattern = re.escape(output).replace('\%\(version\)s', '(\\w+)')
          if re.match(pattern, path):
            return bundle
        if hasattr(bundle, 'contents'):
          children = get_bundle_from_output(path, bundle.contents)
          if children:
            return children

    @app.before_request
    def livereload():
      if 'livereload' in request.args:
        path = os.path.relpath(request.path, assets_env.url)
        bundle = get_bundle_from_output(path, assets_env)
        if bundle:
          __logger__.debug('Building %s', bundle)
          bundle.build(env=assets_env)
          url = bundle.urls(env=assets_env)[0]
          if url.split('?')[0] != request.path:
            __logger__.debug('Url changed, redirecting to %s', url)
            return redirect(url)
        else:
          __logger__.debug('No bundle found for %s', path)

  if app.config.get('GZIP'):
    gzip.init_app(app)

  if app.config.get('USE_REDIS_QUEUE'):
    redis_connection.init_app(host=app.config['CACHE_REDIS_HOST'],
        port=app.config['CACHE_REDIS_PORT'],
        password=app.config.get('CACHE_REDIS_PASSWORD'))


def configure_logging(app):
  """Configures logging."""
  # This makes it sure the logger is created before configuration.
  app.logger
  # Now configure
  logging.config.dictConfig(app.config['LOGGING'])
  __logger__.info('Logging configured')
