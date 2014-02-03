#! /usr/bin/env python
"""
    cpucoolerchart.command
    ~~~~~~~~~~~~~~~~~~~~~~

    Various commands to manage the database. You can run the commands by typing
    ``cpucoolerchart [command]`` if you've installed the package, or
    ``python manage.py [command]`` if you've downloaded the source.

    .. autofunction:: main

    The following functions are commands that can be run from command line.
    Normally you do not call these functions directly in Python modules, but if
    you want here is an example::

        from cpucoolerchart.app import create_app
        from cpucoolerchart.command import update
        app = create_app()  # or any app that you've created before
        with app.app_context():
            update(force=True)

    .. autofunction:: update
    .. autofunction:: createdb
    .. autofunction:: dropdb
    .. autofunction:: resetdb
    .. autofunction:: clearcache
    .. autofunction:: export
    .. autofunction:: danawa

"""

from __future__ import print_function
import sys

from flask import current_app
from flask.ext.script import Manager, prompt_bool
import rq

from .app import create_app
from .crawler import update_data, print_danawa_results
from .extensions import db, cache, redis, update_queue
from .models import Maker, Heatsink, FanConfig, Measurement
from .views import export_data


#: The command manager
manager = Manager(create_app)


@manager.shell
def _make_shell_context():
    """Returns shell context with frequently used objects."""
    return dict(app=current_app, db=db, cache=cache, redis=redis,
                update_queue=update_queue, Maker=Maker, Heatsink=Heatsink,
                FanConfig=FanConfig, Measurement=Measurement)


@manager.command
def update(force=False):
    """Updates the database with data fetched from remote sources (Coolenjoy
    and Danawa). If --force is used, always update the database even if it is
    done recently. Note that even if --force is used, the updated data might
    not be up-to-date since responses from remote sources are cached. If you
    really want to make sure the data is fresh, run ``clearcache`` before this
    command.

    """
    update_data(force)


@manager.command
def runworker(burst=False):
    """Run a worker that processes jobs in the update queue. If --burst is
    used, the worker exits after finishing all the jobs in the queue. It waits
    for a job in an endless loop and processes it by default.

    """
    current_app.logger.info('runworker called with burst=%s', burst)
    with rq.Connection(connection=redis):
        worker = rq.Worker([update_queue])
        # Remove the default exception handler that moves job to the failed
        # queue. Our jobs are not so important to be inspected later.
        worker.pop_exc_handler()
        worker.work(burst=burst)


@manager.command
def createdb():
    """Creates tables in the database. It first checks for the existence of
    each individual table, and if not found will issue the CREATE statements.

    """
    db.create_all()


@manager.command
def dropdb():
    """Drops all database tables."""
    try:
        if prompt_bool("Are you sure you want to lose all your data"):
            db.drop_all()
    except Exception:
        pass


@manager.command
def resetdb():
    """Drops and creates all database tables. It's just a shortcut for dropdb
    and createdb in succession.

    """
    dropdb()
    createdb()


@manager.command
def clearcache():
    """Clears the cache which may contain returned HTML pages from Coolenjoy,
    the time when the database was updated, etc.

    """
    cache.clear()


@manager.command
def export(delim=','):
    """Prints all data in a comma-separated format. Use --delim to change the
    delimeter to other than a comma.

    """
    if delim == '\\t':
        delim = '\t'
    print(export_data(delim))


@manager.command
def danawa():
    """Searches Danawa for heatsinks that don't have entries in
    :data:`~cpucoolerchart.crawler_data.DANAWA_ID_MAPPING` and prints results.
    It is useful during development to find missing Danawa identifiers for
    heatsinks.

    """
    print_danawa_results()


def main(app=None):
    """Runs the command manager that parses the command line arguments and
    executes the given command. If *app* is not given, it will create a new
    app using :func:`~cpucoolerchart.app.create_app`.

    """
    if app is not None:
        manager.app = app
    manager.run()


if __name__ == '__main__':
    main()
