"""
    cpucoolerchart.extensions
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Contains Flask extension objects used by the CPU Cooler Chart app.

"""

from flask.ext.cache import Cache
from flask.ext.sqlalchemy import SQLAlchemy


__all__ = ['db', 'cache']


#: Flask-SQLAlchemy__ instance
#:
#: __ http://pythonhosted.org/Flask-SQLAlchemy/
db = SQLAlchemy()

#: Flask-Cache__ instance
#:
#: __ http://pythonhosted.org/Flask-Cache/
cache = Cache()
