#! /usr/bin/env python
from flask.ext.script import Manager, prompt_bool
from cpucoolerchart import create_app
from cpucoolerchart.extensions import db, cache
from cpucoolerchart.fetch import update_data
from cpucoolerchart.models import Maker, Heatsink, FanConfig, Measurement
from cpucoolerchart.util import heroku_scale


app = create_app()
manager = Manager(app)


@manager.shell
def make_shell_context():
  """Returns shell context with common objects and classes."""
  return dict(app=app, db=db, cache=cache, Maker=Maker, Heatsink=Heatsink,
      FanConfig=FanConfig, Measurement=Measurement)


@manager.command
def export(csv=False, delim=','):
  """
  Prints data in the database in a single table. It prints data in a
  pretty-formatted table by default. If --csv is specified, data will be
  comma-separated. Use --delim to change the delimeter to other than a comma.

  """
  print 'not implemented yet'

@manager.command
def update(force=False):
  """
  Updates the database with data fetched from remote sources (Coolenjoy and
  Danawa). If --force is used, always update the database even if it is done
  recently. Note that the fetched data are cached for 1 day, so it may not be
  up-to-date.

  """
  try:
    update_data(force)
  finally:
    if app.config.get('REDIS_QUEUE_BURST_MODE_IN_HEROKU'):
      heroku_scale('worker', 0)


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
  dropdb()
  createdb()


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


if __name__ == '__main__':
  manager.run()
