#! /usr/bin/env python
from __future__ import print_function
import sys

from flask.ext.script import Manager, prompt_bool
from cpucoolerchart.app import (app, db, cache, Maker, Heatsink, FanConfig,
                                Measurement, export_data)
from cpucoolerchart.crawler import update_data, print_danawa_results


manager = Manager(app)


@manager.shell
def make_shell_context():
    """Returns shell context with frequently used objects."""
    return dict(app=app, db=db, cache=cache, Maker=Maker, Heatsink=Heatsink,
                FanConfig=FanConfig, Measurement=Measurement)


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
    recently. Note that the fetched data are cached for 1 day, so it may not be
    up-to-date.

    """
    update_data(force)


@manager.command
def danawa():
    """
    Prints danawa search results. Use this command to find danawa product
    identifiers for heatsink models.

    """
    print_danawa_results()


db_manager = Manager(help="Makes changes to the database.")
manager.add_command('db', db_manager)


@db_manager.command
def create():
    """
    Creates tables in the database. It first checks for the existence of each
    individual table, and if not found will issue the CREATE statements.

    """
    db.create_all()


@db_manager.command
def drop():
    """Drops all database tables."""
    try:
        if prompt_bool("Are you sure you want to lose all your data"):
            db.drop_all()
    except Exception:
        pass


@db_manager.command
def reset():
    """drop then create"""
    drop()
    create()


cache_manager = Manager(help="Manipulates the cache.")
manager.add_command('cache', cache_manager)


@cache_manager.command
def clear():
    """
    Clears the cache which may contain returned HTML pages from Coolenjoy,
    the time when the database was updated, etc.

    """
    cache.clear()


if __name__ == '__main__':
    manager.run()
