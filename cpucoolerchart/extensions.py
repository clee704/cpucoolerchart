"""
    cpucoolerchart.extensions
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Contains Flask extension objects used by the app.

"""

from flask.ext.cache import Cache
from flask.ext.sqlalchemy import SQLAlchemy


__all__ = ['db', 'cache']


db = SQLAlchemy()
cache = Cache()
