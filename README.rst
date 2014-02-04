CPU Cooler Chart
================

.. image:: https://travis-ci.org/clee704/cpucoolerchart.png?branch=master
   :target: https://travis-ci.org/clee704/cpucoolerchart

CPU Cooler Chart (CCC) is CPU cooler performance and price database.
It merges data from CPU cooler performance measurements and price information
from Coolenjoy and Danawa.

CPU Cooler Chart is comprised of two parts, the API server part (this project)
and the web client part. You can find the web part at
`github.com/clee704/cpucoolerchart-web`_.

.. _github.com/clee704/cpucoolerchart-web: https://github.com/clee704/cpucoolerchart-web


Install
-------

CPU Cooler Chart depends on lxml_, which in turn depends on liblxml2
and libxslt. You can install these with following commands.

- Debian/Ubuntu: ``sudo apt-get install libxml2-dev libxslt1-dev``
- Mac OS X (with Homebrew_): ``brew install libxml2 libxslt``

For more information, see `Installing lxml`_.

If you are ready to install lxml, you can install CPU Cooler Chart. There are
many ways to do that but using pip is recommended:

.. code-block:: console

    $ pip install --pre cpucoolerchart

Currently ``--pre`` argument is needed but it will be unnecessary once a
non-developmental release is out.

.. _lxml: http://lxml.de
.. _Homebrew: http://brew.sh
.. _Installing lxml: http://lxml.de/installation.html


Running
-------

Before running the web server, you must initialize a database:

.. code-block:: console

    $ cpucoolerchart createdb

It will make a SQLite database at ``instance/development.db`` under the current
directory. Although not tested, there is no restrictions on the choice of
the database to use as long as SQLAlchemy_ supports it. See Configuration_ for
how to change database options.

Now the database is ready and empty. Run the following command to fill it with
data:

.. code-block:: console

    $ cpucoolerchart update

It will fetch measurement data from Coolenjoy_. It might spit out some
warnings due to inconsistencies in the data or because you haven't provided
Danawa_ API keys. Nothing is a serious problem for now.

To see the data, first you need to run a web server:

.. code-block:: console

    $ cpucoolerchart runserver

It will run a development server at port 5000. Open your browser and go to
``http://localhost:5000/makers``. It should show some heatsink makers in JSON
format. Go to ``http://localhost:5000/all`` to download a CSV file that
contains all data. For the complete list of HTTP APIs, see `the docs`__.
Meanwhile, you can read `views.py`_ file for what's there.

For production, there are `many options`_ to run a web server (you should not
use the development server in production). CPU Cooler Chart is built with
Flask_, which means it's WSGI-compatible. The endpoint is
``cpucoolerchart.wsgi:app``. Or you can make a custom Python file and create an
app there:

.. code-block:: python

    from cpucoolerchart.app import create_app
    app = create_app({
        'SQLALCHEMY_DATABASE_URI': 'postgres://user:pass@somewhere:5432/ccc'
    })

.. _SQLAlchemy: http://www.sqlalchemy.org
.. _Configuration: http://cpucoolerchart.readthedocs.org/en/latest/#configuration
.. _Coolenjoy: http://www.coolenjoy.net
.. _Danawa: http://danawa.co.kr
.. _views.py: cpucoolerchart/views.py
__ Documentation_
.. _many options: http://flask.pocoo.org/docs/deploying/
.. _Flask: http://flask.pocoo.org


Links
-----

- `GitHub repository`_
- Documentation_
- `CPU Cooler Chart`_ (deployed site)

.. _GitHub repository: https://github.com/clee704/cpucoolerchart
.. _Documentation: http://cpucoolerchart.readthedocs.org
.. _CPU Cooler Chart: http://cpucoolerchart.clee.kr


License
-------

CPU Cooler Chart is licensed under the MIT License. See LICENSE_ for more.

.. _LICENSE: LICENSE
