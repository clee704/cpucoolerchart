#! /usr/bin/env python
"""
    cpucoolerchart.command
    ~~~~~~~~~~~~~~~~~~~~~~

    Various commands to manage the database. You can run the commands by typing
    ``cpucoolerchart [command]`` if you've installed the package, or
    ``python command.py [command]`` if you've downloaded the source.

"""

from __future__ import print_function
import sys

from flask import current_app
from flask.ext.script import Manager, prompt_bool

from .app import create_app
from .crawler import update_data, print_danawa_results
from .extensions import db, cache
from .models import Maker, Heatsink, FanConfig, Measurement
from .views import export_data


manager = Manager(create_app)


@manager.shell
def make_shell_context():
    """Returns shell context with frequently used objects."""
    return dict(app=current_app, db=db, cache=cache, Maker=Maker,
                Heatsink=Heatsink, FanConfig=FanConfig,
                Measurement=Measurement)


@manager.command
def export(delim=','):
    """
    Prints all data in a comma-separated format. Use --delim to change the
    delimeter to other than a comma.

    """
    if delim == '\\t':
        delim = '\t'
    print(export_data(delim))


@manager.command
def update(force=False):
    """
    Updates the database with data fetched from remote sources (Coolenjoy and
    Danawa). If --force is used, always update the database even if it is done
    recently. Note that even if --force is used, the updated data might not be
    up-to-date since responses from remote sources are cached. If you really
    want to make sure the data is fresh, run this command after running
    ``clearcache``.

    """
    update_data(force)


@manager.command
def danawa():
    """
    Prints danawa search results. Use this command to find danawa product
    identifiers for heatsink models.

    """
    print_danawa_results()


@manager.command
def createdb():
    """
    Creates tables in the database. It first checks for the existence of each
    individual table, and if not found will issue the CREATE statements.

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
    """drop then create"""
    drop()
    create()


@manager.command
def clearcache():
    """
    Clears the cache which may contain returned HTML pages from Coolenjoy,
    the time when the database was updated, etc.

    """
    cache.clear()


def main(app=None):
    if app is not None:
        manager.app = app
    manager.run()


if __name__ == '__main__':
    main()