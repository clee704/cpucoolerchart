#! /usr/bin/env python
from flask.ext.script import Manager, prompt_bool
from cpucoolerchart import create_app
from cpucoolerchart.extensions import db, cache
from cpucoolerchart.fetch import update, fetch_and_print_data
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
def printdata():
  """
  Fetches data from remote sources (Coolenjoy and Danawa) and print them in a
  table. Note that the data are cached for 1 day, so it may not be up-to-date.

  """
  fetch_and_print_data()


@manager.command
def updatedata(force=False):
  """
  Fetches data from remote sources (Coolenjoy and Danawa) and update the local
  database. If --force is used, always update data even if it is done recently.
  Note that the data are cached for 1 day, so it may not be up-to-date.

  """
  try:
    update(force)
  finally:
    if app.config.get('REDIS_QUEUE_BURST_MODE_IN_HEROKU'):
      heroku_scale('worker', 0)


@manager.command
def createdb():
  """
  Creates database tables. First check for the existence of each individual
  table, and if not found will issue the CREATE statements.

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
  """Drops and creates all database tables."""
  dropdb()
  createdb()


@manager.command
def clearcache():
  """
  Clear the cache which may contain returned HTML pages from Coolenjoy, HTTP
  responses that this web server generated, the time when the database was
  updated, etc.

  """
  cache.clear()


if __name__ == '__main__':
  manager.run()
