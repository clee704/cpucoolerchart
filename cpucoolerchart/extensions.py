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

import zlib
from werkzeug.contrib.cache import RedisCache

class CompressedRedisCache(RedisCache):

  def dump_object(self, value):
    serialized_str = RedisCache.dump_object(self, value)
    try:
      return zlib.compress(serialized_str)
    except zlib.error:
      return serialized_str

  def load_object(self, value):
    try:
      serialized_str = zlib.decompress(value)
    except (zlib.error, TypeError):
      serialized_str = value
    return RedisCache.load_object(self, serialized_str)
