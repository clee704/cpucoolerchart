import logging
import re

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
