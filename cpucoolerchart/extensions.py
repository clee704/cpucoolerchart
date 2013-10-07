from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy()


from flask.ext.cache import Cache
cache = Cache()


from flask.ext.assets import Environment
assets_env = Environment()


from flask.ext.gzip import Gzip

class MyGzip(Gzip):
  def __init__(self):
    pass

  def init_app(self, app):
    Gzip.__init__(self, app)

  def after_request(self, response):
    # Fix https://github.com/elasticsales/Flask-gzip/issues/7
    response.direct_passthrough = False
    return super(MyGzip, self).after_request(response)

gzip = MyGzip()


try:
  from redis import Redis

  class MyRedis(Redis):
    def __init__(self):
      pass
    def init_app(self, *args, **kwargs):
      Redis.__init__(self, *args, **kwargs)

  redis_connection = MyRedis()
except ImportError:
  redis_connection = None
