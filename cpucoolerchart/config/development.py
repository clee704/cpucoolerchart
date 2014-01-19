from copy import deepcopy
import os

from ..config import DefaultConfig


class Config(DefaultConfig):
  DEBUG = True
  SQLALCHEMY_DATABASE_URI = 'postgres://cpucoolerchart:8LcVJ3DQJHXjDo@localhost/cpucoolerchart'
  CACHE_TYPE = 'redis'
  CACHE_REDIS_HOST = 'localhost'
  CACHE_REDIS_PORT = 6379
  URL_ROOT = 'http://localhost:5000/'
  LOGGING = deepcopy(DefaultConfig.LOGGING)
  LOGGING['loggers']['cpucoolerchart']['level'] = os.environ.get('LOG_LEVEL', 'DEBUG')
  LOGGING['loggers']['sqlalchemy.engine']['level'] = os.environ.get('SQL_LOG_LEVEL', 'WARNING')

Config.from_envvars()
