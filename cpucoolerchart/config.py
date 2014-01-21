"""
    cpucoolerchart.config
    ~~~~~~~~~~~~~~~~~~~~~

    Defines the default configuration values.
"""

import os
import re


class Config(object):
    """The default configuration values."""

    DEBUG = False
    TESTING = False

    SQLALCHEMY_DATABASE_URI = 'sqlite://'    # In-memory database

    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 3600 * 3    # 3 hours
    CACHE_KEY_PREFIX = 'cpucoolerchart:'
    CACHE_COMPRESSION = True

    UPDATE_INTERVAL = 86400 * 3    # 3 days

    URL_ROOT = 'http://cpucoolerchart.yourdomain.com/'
    ACCESS_CONTROL_ALLOW_ORIGIN = '*'

    DANAWA_API_KEY_PRODUCT_INFO = None
    DANAWA_API_KEY_SEARCH = None
    HEROKU_API_KEY = None

    MAIL_TOADDRS = None
    GMAIL_USERNAME = None
    GMAIL_PASSWORD = None

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

    @classmethod
    def from_envvars(cls):
        """Updates config values from environment variables."""
        for key in os.environ:
            if re.match(r'^LOGGING(\.([a-z0-9_]+|"[a-z0-9_.]+"))+$', key):
                i = len('LOGGING.')
                d = cls.LOGGING
                while True:
                    if key[i] == '"':
                        j = key.find('"', i + 1)
                        if j == -1:
                            raise RuntimeError('unmatched quote')
                        k = key[i + 1:j]
                        i = j + 2
                    else:
                        j = key.find('.', i + 1)
                        if j == -1:
                            j = len(key)
                        k = key[i:j]
                        i = j + 1
                    if i >= len(key):
                        break
                    if k in d:
                        d = d[k]
                    else:
                        d[k] = {}
                        d = d[k]
                d[k] = decode(os.environ[key])
            elif re.match(r'^[A-Z_]+$', key):
                setattr(cls, key, decode(os.environ[key]))

    @classmethod
    def setup_gmail_smtp(cls):
        """Setups Gmail SMTP server so that admins are notified when an error
        occurs."""
        keys = ['MAIL_TOADDRS', 'GMAIL_USERNAME', 'GMAIL_PASSWORD']
        if not all(getattr(cls, key) for key in keys):
            return
        smtp_handler = cls.LOGGING['handlers']['mail_admins']
        smtp_handler['toaddrs'] = cls.MAIL_TOADDRS
        smtp_handler['mailhost'] = ('smtp.gmail.com', 587)
        smtp_handler['credentials'] = (cls.GMAIL_USERNAME, cls.GMAIL_PASSWORD)
        smtp_handler['secure'] = ()
        cls.LOGGING['loggers']['cpucoolerchart']['handlers'].append(
            'mail_admins')


def decode(text):
    """Returns a Python value from the given string. Not good nor rigid
    decoding scheme but convenient one for getting values from environment.
    """
    if re.match(r'^\d+$', text):
        return int(text)
    elif re.match(r'^\d+\.\d+$', text):
        return float(text)
    elif text == 'True':
        return True
    elif text == 'False':
        return False
    elif re.match(r'^\[.*\]$', text):
        # Example: "[a, b, c]" => ['a', 'b', 'c']
        return re.split(r'\s*,\s*', text[1:-1])
    else:
        # If all others fail, just use the plain string.
        return text
