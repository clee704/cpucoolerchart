from copy import deepcopy

from ..config import DefaultConfig


class Config(DefaultConfig):
  DEBUG = True
  ASSETS_DEBUG = True
  LIVE_RELOAD = True
  SQLALCHEMY_DATABASE_URI = 'postgres://cpucoolerchart:8LcVJ3DQJHXjDo@localhost/cpucoolerchart'
  CACHE_TYPE = 'redis'
  CACHE_REDIS_HOST = 'localhost'
  CACHE_REDIS_PORT = 6379
  USE_REDIS_QUEUE = True
  LOGGING = deepcopy(DefaultConfig.LOGGING)
  LOGGING['loggers']['cpucoolerchart']['level'] = 'DEBUG'
  LOGGING['loggers']['sqlalchemy.engine']['level'] = 'INFO'

Config.from_envvars()
