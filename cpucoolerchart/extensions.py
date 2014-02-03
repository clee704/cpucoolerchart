"""
    cpucoolerchart.extensions
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Contains Flask extension objects used by the CPU Cooler Chart app.

"""

from flask.ext.cache import Cache
from flask.ext.sqlalchemy import SQLAlchemy
from redis import Redis as BaseRedis
from rq import Queue

from ._compat import urllib


#: Flask-SQLAlchemy__ instance
#:
#: __ http://pythonhosted.org/Flask-SQLAlchemy/
db = SQLAlchemy()

#: Flask-Cache__ instance
#:
#: __ http://pythonhosted.org/Flask-Cache/
cache = Cache()


class Redis(BaseRedis):
    """Extends :class:`redis.Redis` so that it works with Flask app. If *app*
    is specified, a connection is initialized with :meth:`init_app`.

    """

    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initializes a Redis connection. The following configuration values
        are read from ``app.config``:

        .. list-table::
           :widths: 20 80
           :header-rows: 1

           * - name
             - description
           * - ``RQ_HOST``
             - Redis server host.
           * - ``RQ_PORT``
             - Redis server port. Default is 6379.
           * - ``RQ_DB``
             - Redis db (zero-based number index). Default is 0.
           * - ``RQ_PASSWORD``
             - Redis server password.
           * - ``RQ_URL``
             - Redis URL that can specify host, port, db, password in a single
               value. Example: ``redis://user:password@host:6379/0``. If
               defined, it overrides all the other values above.

        """
        if app.config.get('RQ_URL'):
            url = urllib.parse.urlparse(app.config['RQ_URL'])
            assert url.scheme == 'redis' or not url.scheme
            host = url.hostname
            port = int(url.port or 6379)
            try:
                db = int(url.path.replace('/', ''))
            except (AttributeError, ValueError):
                db = 0
            password = url.password
        else:
            host = app.config.get('RQ_HOST')
            port = int(app.config.get('RQ_PORT') or 6379)
            db = int(app.config.get('RQ_DB') or 0)
            password = app.config.get('RQ_PASSWORD')
        BaseRedis.__init__(self, host=host, port=port, db=db,
                           password=password)


#: :class:`Redis` instance
redis = Redis()


#: A Redis queue that is used to update data
update_queue = Queue('update', connection=redis, default_timeout=600)
