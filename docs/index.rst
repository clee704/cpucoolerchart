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

See `the GitHub repo page`__.

__ https://github.com/clee704/cpucoolerchart


HTTP APIs
---------

All endpoints returning a list of items in JSON format returns an object
containing two properties *count* and *items*. *count* is the number of
items in the *items* array. The order of items is undefined and may not in the
same order for each request.

.. autoflask:: cpucoolerchart.app:create_app(config='app.cfg')
   :undoc-static:


References
----------

.. toctree::
   :maxdepth: 2

   references


License
-------

CPU Cooler Chart is licensed under the MIT License. See LICENSE__ for more.

__ https://github.com/clee704/cpucoolerchart/blob/master/LICENSE
