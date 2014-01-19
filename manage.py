#! /usr/bin/env python
import sys

from flask.ext.script import Manager, prompt_bool
from cpucoolerchart import create_app
from cpucoolerchart.extensions import db, cache
from cpucoolerchart.fetch import update_data, print_danawa_results, export_data
from cpucoolerchart.models import Maker, Heatsink, FanConfig, Measurement
from cpucoolerchart.util import heroku_scale, print_utf8


app = create_app()
manager = Manager(app)


@manager.shell
def make_shell_context():
  """Returns shell context with common objects and classes."""
  return dict(app=app, db=db, cache=cache, Maker=Maker, Heatsink=Heatsink,
      FanConfig=FanConfig, Measurement=Measurement)


@manager.command
def export(delim=','):
  """
  Prints data in a comma-separated format. Use --delim to change the delimeter
  to other than a comma.

  """
  if delim == '\\t':
    delim = '\t'
  print_utf8(export_data(delim))


@manager.command
def update(force=False, quit_worker=False):
  """
  Updates the database with data fetched from remote sources (Coolenjoy and
  Danawa). If --force is used, always update the database even if it is done
  recently. Note that the fetched data are cached for 1 day, so it may not be
  up-to-date.

  If --quit_worker is set, it scales back the heroku worker process after it
  is done.

  """
  try:
    update_data(force)
  finally:
    if quit_worker:
      heroku_scale('worker', 0)


@manager.command
def danawa():
  """
  Prints danawa search results. Use this command to find danawa product
  identifiers for heatsinks.

  """
  print_danawa_results()


db_manager = Manager(help="Makes changes to the database.")
manager.add_command('db', db_manager)


@db_manager.command
def create():
  """
  Creates database tables. First check for the existence of each individual
  table, and if not found will issue the CREATE statements.

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
  """Drops and creates all database tables."""
  drop()
  create()


cache_manager = Manager(help="Manipulates the cache.")
manager.add_command('cache', cache_manager)


@cache_manager.command
def clear():
  """
  Clears the cache which may contain returned HTML pages from Coolenjoy, HTTP
  responses that this web server generated, the time when the database was
  updated, etc.

  """
  cache.clear()


@cache_manager.command
def delete(kind):
  """Deletes cached data of the given kind. Possible values: html, json"""
  if kind == 'html':
    cache.delete('view:/')
  elif kind == 'json':
    cache.delete('view:/makers')
    cache.delete('view:/heatsinks')
    cache.delete('view:/fan-configs')
    cache.delete('view:/measurements')
  else:
    print >>sys.stderr, u'invalid value for kind: {0} (possible values are: html, json)'.format(kind)
    return 1


if __name__ == '__main__':
  manager.run()
