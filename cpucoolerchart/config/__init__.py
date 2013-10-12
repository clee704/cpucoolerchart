import os
import re


__all__ = ['development', 'test', 'production']
__project_root__ = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))


class DefaultConfig(object):
  DEBUG = False
  UPDATE_INTERVAL = 86400 * 3
  SEND_FILE_MAX_AGE_DEFAULT = 31536000
  GZIP = True
  ASSETS_URL = '/static'
  LIVE_RELOAD = False
  CACHE_KEY_PREFIX = 'cpucoolerchart:'
  CACHE_TYPE = 'simple'
  CACHE_DEFAULT_TIMEOUT = 3600
  CACHE_COMPRESSION = True
  LOGGER_NAME = 'cpucoolerchart'
  LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
      'default': {
        'format': '%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S',
      },
      'raw': {
        'format': '%(message)s'
      },
    },
    'handlers': {
      'console': {
        'level': 'DEBUG',
        'class': 'logging.StreamHandler',
        'formatter': 'default',
      },
      'console_raw': {
        'level': 'DEBUG',
        'class': 'logging.StreamHandler',
        'formatter': 'raw',
      },
      'mail_admins': {
        'level': 'ERROR',
        'formatter': 'default',
        'class': 'logging.handlers.SMTPHandler',
        'toaddrs': [],
        'fromaddr': 'ccc-logger@localhost',
        'subject': 'Logging',
        'mailhost': 'localhost',
      },
      'null': {
        'class': 'logging.NullHandler',
      },
    },
    'loggers': {
      'cpucoolerchart': {
        'handlers': ['console'],
        'level': 'WARNING',
      },
      'sqlalchemy.engine': {
        'handlers': ['console'],
        'level': 'WARNING',
      },
      'gunicorn.access': {
        'handlers': ['console_raw'],
        'level': 'INFO',
      },
    }
  }
  LESS_BIN = os.path.join(__project_root__, 'node_modules/.bin/lessc')

  @classmethod
  def from_envvars(cls):
    for key in os.environ:
      if validkey(key):
        setattr(cls, key, autocast(os.environ[key]))

def validkey(key):
  return re.match(r'^[A-Z_]+$', key)

def autocast(value):
  if re.match(r'^\d+$', value):
    return int(value)
  elif re.match(r'^\d+\.\d+$', value):
    return float(value)
  elif value == 'True':
    return True
  elif value == 'False':
    return False
  elif re.match(r'^\[.*\]$', value):
    # Example: "[a, b, c]" => ['a', 'b', 'c']
    return re.split(r'\s*,\s*', value[1:-1])
  else:
    # If all others fail, just use the plain string.
    return value

DefaultConfig.from_envvars()
