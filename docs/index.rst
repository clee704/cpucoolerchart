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

    $ pip install cpucoolerchart

See `the GitHub repo page`__ for more.

__ https://github.com/clee704/cpucoolerchart


Config
------

TBD


HTTP APIs
---------

All endpoints returning a list of items in JSON format returns an object
containing two properties *count* and *items*. *count* is the number of
items in the *items* array. The order of items is undefined and may not in the
same order for each request. Properties of an item is described in a table.
When there is an asterisk at the end of a property name, it means
that the property may have ``null`` as its value.

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
