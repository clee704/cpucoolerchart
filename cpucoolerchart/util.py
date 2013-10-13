import logging
import os
import re
import subprocess
import urlparse

from flask import current_app, abort
import heroku
import requests

from .config import __project_root__
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


# from lxml@d441222/src/lxml/apihelpers.pxi:576-588
RE_XML_ENCODING =  re.compile(
    ur'^(<\?xml[^>]+)\s+encoding\s*=\s*["\'][^"\']*["\'](\s*\?>|)', re.U)
HAS_XML_ENCODING = lambda s: RE_XML_ENCODING.match(s) is not None
REPLACE_XML_ENCODING = lambda s: RE_XML_ENCODING.sub(ur'\g<1>\g<2>', s)

def strip_xml_encoding(string):
  if HAS_XML_ENCODING(string):
    return REPLACE_XML_ENCODING(string)
  else:
    return string


def urlpath(url):
  parts = urlparse.urlsplit(url)
  path = parts.path
  if parts.query:
      path += '?' + parts.query
  if parts.fragment:
      path += '#' + parts.fragment
  return path


def take_snapshot():
  phantomjs_bin = os.path.join(__project_root__, 'node_modules/.bin/phantomjs')
  script = os.path.join(__project_root__, 'snapshot.js')
  url = current_app.config.get('URL_ROOT')
  if not url:
    __logger__.warning('Cannot take a snapshot; URL_ROOT is not set.')
    return abort(500)
  return subprocess.check_output([phantomjs_bin, script, url])


def print_utf8(x):
  if isinstance(x, unicode):
    print x.encode('UTF-8')
  else:
    print x
