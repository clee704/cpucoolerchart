CPU Cooler Chart
================

CPU Cooler Chart (CCC) is CPU cooler performance and price database.
It merges data from CPU cooler performance measurements and price information
from Coolenjoy and Danawa.


Compatiblity
------------

CPU Cooler Chart supports Python 2.6, 2.7, and 3.3 on CPython.


Install & Running
-----------------

.. code-block:: console

    $ pip install --pre cpucoolerchart

See `the GitHub repo page`__ for more.

__ https://github.com/clee704/cpucoolerchart


Configuration
-------------

CPU Cooler Chart is configured the same way a Flask app is configured. In
short, there are two ways to configure the app:

- Make a Python file that contains the configuration values and set the
  ``CPUCOOLERCHART_SETTINGS`` environment variable to the path of the file.
  For example, save the following as ``settings.py``:

  .. code-block:: python

      SQLALCHEMY_DATABASE_URI = 'sqlite://'
      CACHE_TYPE = 'simple'

  and set the ``CPUCOOLERCHART_SETTINGS`` environment variable to
  ``/path/to/settings.py`` before running the app.
- Pass a :class:`collections.Mapping` to :func:`~cpucoolerchart.app.create_app`
  when creating the app. Example:

  .. code-block:: python

      from cpucoolerchart.app import create_app
      app = create_app({
          'SQLALCHEMY_DATABASE_URI': 'sqlite://',
          'CACHE_TYPE': 'simple',
      })

See `Configuration Handling`__ for more about configuring a Flask app. In
addition to the Flask builtin configuration values, you can use the following
configuration values that are specific to CPU Cooler Chart:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - name
     - description
   * - SQLALCHEMY_DATABASE_URI
     - (:class:`str`) The database URI that should be used for the database
       connection. Examples:

       - ``sqlite:////tmp/test.db``
       - ``mysql://username:password@server/db``

       For more information about configuration SQLAlchemy, see
       `the Flask-SQLAlchemy documentation`__. Default is
       ``"sqlite:///{INSTANCE_PATH}/development.db"`` where ``{INSTANCE_PATH}``
       is interpreted as the absolute path to the ``instance`` directory under
       the current working directory.
   * - CACHE_TYPE
     - (:class:`str`) Specifies which type of caching object to use. This is an
       import string for a function that will return a
       :class:`werkzeug.contrib.cache.BaseCache` object, or a special short
       names for built-in types. For more information, see
       `the Flask-Cache documentation`__. Default is ``"filesystem"``.
   * - ACCESS_CONTROL_ALLOW_ORIGIN
     - (:class:`str`) A comma-separated list of URIs that may access the
       CORS-enabled endpoints. Default is ``"*"``.
   * - UPDATE_INTERVAL
     - (:class:`int`) A number of seconds for which data is considered up to
       date after an update. Default is ``86400``, which is equivalent to
       one day.
   * - DANAWA_API_KEY_PRODUCT_INFO
     - (:class:`str` or ``None``) Danawa API key for product info. Used to get
       the current prices. Default is ``None``, which logs a warning when it
       tries to get price info.
   * - DANAWA_API_KEY_SEARCH
     - (:class:`str` or ``None``) Danawa API key for search. Used during
       development to find Danawa product identifiers, thus not needed in a
       normal operation. Default is ``None``.
   * - USE_QUEUE
     - (:class:`bool`) Enable enquequing an update job via HTTP. Default is
       ``False``.
   * - RQ_URL
     - (:class:`str` or ``None``) A Redis URL used when ``USE_QUEUE`` is
       ``True``. There are separate configuration values such as ``RQ_HOST``
       and ``RQ_PORT`` that can be used instead of ``RQ_URL``. See
       :meth:`Redis.init_app() <cpucoolerchart.extensions.Redis.init_app>` for
       more.
   * - START_WORKER_NODE
     - (:class:`str` or ``None``) Enable starting a worker node via HTTP. Since
       update occurs infrequently, it is often desirable to run a worker only
       when it is needed. Currently the only supported value is ``"heroku"``.
       Default is ``None``, which disables this feature.
   * - HEROKU_WORKER_NAME
     - (:class:`str`) The name of the worker process as written in
       ``Procfile``. Default is ``"worker"``. The process line should look like
       this::

           worker: cpucoolerchart runworker --burst

       The ``--burst`` argument make the worker process end when it finished
       processing jobs in the update queue.
   * - HEROKU_API_KEY
     - (:class:`str` or ``None``) The Heroku API key
   * - HEROKU_APP_NAME
     - (:class:`str` or ``None``) The Heroku app name

__ http://flask.pocoo.org/docs/config/
__ http://pythonhosted.org/Flask-SQLAlchemy/config.html#configuration-keys
__ http://pythonhosted.org/Flask-Cache/#configuring-flask-cache


HTTP APIs
---------

All endpoints returning a list of items in JSON format returns an object
containing two properties *count* and *items*. *count* is the number of
items in the *items* array. The order of items is undefined and may not in the
same order for each request. Each item has properties described in following
tables. Properties with an asterisk at the end of its name can be ``null``.

Most of the endpoints are CORS enabled using
the :func:`~cpucoolerchart.views.crossdomain` decorator.
The ``Access-Control-Allow-Origin`` response header will be set to the value of
``ACCESS_CONTROL_ALLOW_ORIGIN`` in your config, which is ``"*"`` by default.
For more information about CORS, see `HTTP access control (CORS)`__ on Mozilla
Developer Network.

.. autoflask:: cpucoolerchart.app:create_app(config='app.cfg')
   :undoc-static:

__ https://developer.mozilla.org/en/docs/HTTP/Access_control_CORS


References
----------

.. toctree::
   :maxdepth: 2

   references


License
-------

CPU Cooler Chart is licensed under the MIT License. See LICENSE__ for more.

__ https://github.com/clee704/cpucoolerchart/blob/master/LICENSE
