import logging

from flask import current_app
import heroku
import requests

from .extensions import cache


__logger__ = logging.getLogger(__name__)


def heroku_scale(process_name, qty):
  key = 'heroku:{0}'.format(process_name)
  old_qty = cache.get(key)
  if old_qty == qty:
    return
  # Currently it's not possible to scale processes between 0 and 1 using the
  # public API. Below is a quick-and-dirty workaround for that issue.
  cloud = heroku.from_key(current_app.config['HEROKU_API_KEY'])
  try:
    cloud._http_resource(method='POST',
      resource=('apps', current_app.config['HEROKU_APP_NAME'], 'ps', 'scale'),
      data=dict(type=process_name, qty=qty))
    cache.set(key, qty)
  except requests.HTTPError as e:
    __logger__.error('Could not scale heroku: %s', e.message)


def print_utf8(x):
  if isinstance(x, unicode):
    print x.encode('UTF-8')
  else:
    print x
