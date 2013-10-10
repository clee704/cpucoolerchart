import base64
from collections import namedtuple
from datetime import datetime, timedelta
import itertools
import json
import logging
import math
import os
import re
import sys
import urllib

from flask import current_app
import lxml.etree
import lxml.html
from prettytable import PrettyTable
import requests

from .extensions import db, cache
from .models import Maker, Heatsink, FanConfig, Measurement
from .resources.coolenjoy import MAKER_FIX, MODEL_FIX, INCONSISTENCY_FIX
from .resources.danawa import MAPPING
from .util import strip_xml_encoding


__logger__ = logging.getLogger(__name__)


# Constant for maximum noise level. It is not actually 100 dB; for real values,
# refer to noise_actual_min and noise_actual_max (may be absent).
NOISE_MAX = 100

# Noise levels and CPU power consumptions where the measurements are taken.
NOISE_LEVELS = {35: 4, 40: 3, 45: 2, NOISE_MAX: 1}
CPU_POWER = {62: 1, 92: 2, 150: 3, 200: 4}

SINGLE_TABLE_COLUMNS = [
  'maker', 'model', 'width', 'depth', 'height', 'heatsink_type', 'weight',  # heatsink
  'fan_size', 'fan_thickness', 'fan_count',                                 # fan
  'noise', 'noise_actual_min', 'noise_actual_max', 'rpm_min', 'rpm_max',    # noise / rpm
  'power',                                                                  # power
  'cpu_temp_delta', 'power_temp_delta',                                     # temperature
]

ORDER_BY = ('maker', 'model', 'fan_size', 'fan_thickness', 'fan_count',
    'noise', 'power', 'noise_actual_min')

COLUMN_MAPPING = {
  Maker: ('maker',),
  Heatsink: ('maker', 'model', 'width', 'depth', 'height', 'heatsink_type', 'weight'),
  FanConfig: ('maker', 'model', 'fan_size', 'fan_thickness', 'fan_count'),
  Measurement: ('maker', 'model', 'fan_size', 'fan_thickness', 'fan_count',
      'noise', 'noise_actual_min', 'noise_actual_max', 'rpm_min', 'rpm_max',
      'power', 'cpu_temp_delta', 'power_temp_delta'),
}

# Numeric columns that should be aligned right when printed in a table.
NUMERIC_COLUMNS = [
  'width', 'depth', 'height', 'weight', 'fan_size', 'fan_thickness', 'fan_count',
  'noise', 'noise_actual_min', 'noise_actual_max', 'rpm_min', 'rpm_max', 'power',
  'cpu_temp_delta', 'power_temp_delta',
]

# Theoretical depedencies between columns to check integrity of the original
# data. There should be, if any, very small number of violations of these deps.
# Request corrections to the guy who makes the original data.
DEPENDENCIES = {
  # maker and model determines heatsink properties
  ('maker', 'model'): ('width', 'depth', 'height', 'heatsink_type', 'weight'),

  # maker, model, fan properties, noise and power determines measured values
  ('maker', 'model', 'fan_size', 'fan_thickness', 'fan_count', 'noise', 'power'): (
    'noise_actual_min', 'noise_actual_max', 'rpm_min', 'rpm_max',
    'cpu_temp_delta', 'power_temp_delta'
  )
}


def needs_update():
  last_updated = cache.get('last_updated')
  if not last_updated:
    return True
  interval = current_app.config['UPDATE_INTERVAL']
  return last_updated <= datetime.now() - timedelta(seconds=interval)


def update_data(force=False):
  if not force and not needs_update():
    __logger__.info('Recently updated; nothing to do')
    return
  data_list = fetch_measurement_data()
  update_measurement_data(data_list)
  update_price_data()
  cache.set('last_updated', datetime.now())
  __logger__.info('Successfully updated data from remote sources')


def fetch_measurement_data():
  reset_warnings()
  data_list = []
  for noise in NOISE_LEVELS:
    for power in CPU_POWER:
      if noise != NOISE_MAX and noise <= 40 and power >= 200:
        continue
      try:
        table = get_html_table(noise, power)
      except requests.RequestException:
        __logger__.warning('An error occurred while requesting a page', exc_info=True)
        return []  # Do not return partially fetched data list
      try:
        new_data_list = extract_data(table, noise, power)
      except ParseError:
        return []  # Do not return partially fetched data list
      data_list.extend(new_data_list)
  data_list.sort(key=dictitemgetter(*ORDER_BY))
  data_list = ensure_consistency(data_list)
  return data_list


def get_html_table(noise, power):
  URL_FMT = 'http://www.coolenjoy.net/cooln_db/cpucooler_charts.php?dd={noise}&test={power}'
  html = get_cached_response_text(URL_FMT.format(noise=NOISE_LEVELS[noise], power=CPU_POWER[power]))
  doc = lxml.html.fromstring(html)
  table_xpath = doc.xpath('//table[@width="680"][@bordercolorlight="black"]')
  if not table_xpath:
    raise ParseError('table not found')
  return table_xpath[0]


def extract_data(table, noise, power):
  data_list = []
  for tr in table.xpath('.//tr[@class="tdm"]'):
    data = {}
    cells = tr.xpath('td[not(@width="1")]')
    try:
      data['maker'] = parse_maker(cells[0].text)
      data['model'] = parse_model(cells[0].find('br').tail)
      parse_dimension(data, cells[1].text)
      data['heatsink_type'] = parse_heatsink_type(cells[1].find('br').tail)
      data['weight'] = parse_weight(cells[1].find('br').tail)
      parse_fan_info(data, cells[2].text)
      parse_rpm(data, cells[2].find('br').tail)
      data['noise'] = noise
      if noise == NOISE_MAX:
        parse_noise_actual(data, cells[3].text)
      data['power'] = power
      parse_temp_info(data, cells[3 if noise != NOISE_MAX else 4].xpath('.//font'))
      fix_inconsistency(data)
      data_list.append({k: data[k] for k in data if data[k] is not None})
    except Exception:
      __logger__.exception('An error occurred while parsing a page')
      raise ParseError()
  if not data_list:
    raise ParseError('table rows not found')
  return data_list


def parse_maker(s):
  maker = compress_spaces(s)
  return MAKER_FIX.get(maker.lower(), maker).replace('/', '-')


def parse_model(s):
  model = compress_spaces(s)
  return MODEL_FIX.get(model.lower(), model)


def parse_dimension(data, s):
  if not s or s == '-':
    return
  m = re.search(r'([0-9.]+)\s*x\s*([0-9.]+)\s*x\s*([0-9.]+)', s, re.I)
  if not m:
    warn(u'unrecognizable dimension: {0}'.format(s))
    return
  data['width'] = float(m.group(1))
  data['depth'] = float(m.group(2))
  data['height'] = float(m.group(3))


def parse_heatsink_type(s):
  return compress_spaces(s.split('/')[0].lower())


def parse_weight(s):
  m = re.search(r'([0-9.]+)\s*g', s)
  if not m:
    warn(u'unrecognizable weight: {0}'.format(s))
    return
  weight = float(m.group(1))
  return weight if weight > 0 else None


def parse_fan_info(data, s):
  m = re.search(r'([0-9]+)(?:x([0-9]+))?/([0-9]+)T', s)
  if not m:
    warn(u'unrecognizable fan_info: {0}'.format(s))
    return
  data['fan_size'] = int(m.group(1))
  data['fan_count'] = int(m.group(2)) if m.group(2) is not None else 1
  data['fan_thickness'] = int(m.group(3))


def parse_rpm(data, s):
  m = re.search(r'(?:([0-9]+)(?:\s*-\s*([0-9]+))?)?\s*rpm', s)
  if not m:
    warn(u'unrecognizable rpm: {0}'.format(s))
    return
  if m.group(1) is None:
    return
  base = m.group(1)
  minimum = int(base)
  data['rpm_min'] = minimum
  extra = m.group(2)
  if extra is None:
    data['rpm_max'] = minimum
    return
  elif int(extra) > minimum:
    data['rpm_max'] = int(extra)
  else:
    unit = 10 ** len(extra)
    maximum = (minimum // unit) * unit + int(extra)
    if maximum < minimum:
      maximum += unit
    data['rpm_max'] = maximum
  assert data['rpm_min'] <= data['rpm_max']


def parse_noise_actual(data, s):
  if not s:
    return
  m = re.search(r'([0-9.]+)(?:\s*-\s*([0-9.]+))?', s)
  if not m:
    warn(u'unrecognizable noise_actual: {0}'.format(s))
    return
  base = m.group(1)
  minimum = float(base)
  data['noise_actual_min'] = minimum
  extra = m.group(2)
  if extra is None:
    data['noise_actual_max'] = minimum
    return
  elif re.match(r'^[0-9]{2,}\.[0-9]$', base):
    maximum = None
    if re.match(r'^[0-9]$', extra):
      maximum = float(base.split('.')[0] + '.' + extra)
    elif re.match(r'^[0-9]\.[0-9]$', extra):
      maximum = float(base.split('.')[0][:-1] + extra)
    elif re.match(r'^[0-9]{2,}(\.[0-9]+)?$', extra):
      maximum = float(extra)
    if maximum is not None and minimum < maximum:
      data['noise_actual_max'] = maximum
      return
  warn(u'interpreted unrecognizable noise_actual {0} as {1}'.format(s, minimum))
  data['noise_actual_max'] = minimum
  assert data['noise_actual_min'] <= data['noise_actual_max']


def parse_temp_info(data, elements):
  assert len(elements) == 2
  data['cpu_temp_delta'] = float(elements[0].text_content())
  power_temp_delta = elements[1].text_content()
  if power_temp_delta:
    data['power_temp_delta'] = float(power_temp_delta)


def fix_inconsistency(data):
  key = (data['maker'] + ' ' + data['model']).lower()
  if key in INCONSISTENCY_FIX:
    data.update(INCONSISTENCY_FIX[key])


def ensure_consistency(data_list):
  first_values = {}
  for x in DEPENDENCIES:
    first_values[x] = {}
  new_data_list = []
  for data in data_list:
    remove = False
    for x, y in DEPENDENCIES.iteritems():
      keys = tuple(data.get(k) for k in x)
      values = tuple(data.get(k) for k in y)
      if keys not in first_values[x]:
        first_values[x][keys] = values
      elif first_values[x][keys] != values:
        warn(u'dependency {0} -> {1} violated: {2}: {3} != {4}'.format(
            x, y, keys, first_values[x][keys], values))
        remove = True
    if not remove:
      new_data_list.append(data)
  return new_data_list


def update_measurement_data(data_list):
  groups = itertools.groupby(data_list, dictitemgetter('maker'))
  for maker_name, data_sublist in groups:
    update_maker(data_sublist, maker_name)
  db.session.commit()


def update_maker(data_list, maker_name):
  keys = dict(name=maker_name)
  data = keys
  maker = Maker.query.find(**keys)
  if maker is None:
    maker = Maker(**data)
    db.session.add(maker)
  else:
    maker.update(**data)
  groups = itertools.groupby(data_list, dictitemgetter(
      'model', 'width', 'depth', 'height', 'heatsink_type', 'weight'))
  for heatsink_data, data_sublist in groups:
    update_heatsink(data_sublist, maker, *heatsink_data)


def update_heatsink(data_list, maker, model_name, width, depth, height, heatsink_type, weight):
  keys = dict(name=model_name, maker_id=maker.id)
  data = dict(name=model_name, maker=maker, width=width, depth=depth, height=height,
      heatsink_type=heatsink_type, weight=weight)
  heatsink = Heatsink.query.find(**keys)
  if heatsink is None:
    heatsink = Heatsink(**data)
    db.session.add(heatsink)
  else:
    heatsink.update(**data)
  groups = itertools.groupby(data_list, dictitemgetter(
      'fan_size', 'fan_thickness', 'fan_count'))
  for fan_config_data, data_sublist in groups:
    update_fan_config(data_sublist, heatsink, *fan_config_data)


def update_fan_config(data_list, heatsink, fan_size, fan_thickness, fan_count):
  keys = dict(fan_size=fan_size, fan_thickness=fan_thickness, fan_count=fan_count,
      heatsink_id=heatsink.id)
  data = dict(fan_size=fan_size, fan_thickness=fan_thickness, fan_count=fan_count,
      heatsink=heatsink)
  fan_config = FanConfig.query.find(**keys)
  if fan_config is None:
    fan_config = FanConfig(**data)
    db.session.add(fan_config)
  else:
    fan_config.update(**data)
  for data in data_list:
    update_measurement(fan_config, data)


def update_measurement(fan_config, data):
  keys = subdict(data, 'noise', 'power')
  keys['fan_config_id'] = fan_config.id
  data = subdict(data,
      'noise', 'power', 'noise_actual_min', 'noise_actual_max',
      'rpm_min', 'rpm_max', 'cpu_temp_delta', 'power_temp_delta')
  data['fan_config'] = fan_config
  measurement = Measurement.query.find(**keys)
  if measurement is None:
    measurement = Measurement(**data)
    db.session.add(measurement)
  else:
    measurement.update(**data)


def update_price_data():
  if 'DANAWA_API_KEY_PRODUCT_INFO' not in current_app.config:
    __logger__.warning('DANAWA_API_KEY_PRODUCT_INFO not found')
    return
  api_key = current_app.config['DANAWA_API_KEY_PRODUCT_INFO']
  heatsinks = db.session.query(Maker.name, Heatsink).join(
      Heatsink, Maker.id == Heatsink.maker_id)
  for maker_name, heatsink in heatsinks:
    key = (maker_name + ' ' + heatsink.name).lower()
    if key in MAPPING and MAPPING[key] != heatsink.danawa_id:
      heatsink.danawa_id = MAPPING[key]
    if heatsink.danawa_id is None:
      continue
    url = 'http://api.danawa.com/api/main/product/info'
    query = {'key': api_key, 'mediatype': 'json', 'prodCode': heatsink.danawa_id}
    json_text = get_cached_response_text(url + '?' + urllib.urlencode(query))
    data = load_danawa_json(json_text)
    if data is None:
      continue
    min_price = int(data.get('minPrice', 0))
    if min_price:
      heatsink.price = min_price
  db.session.commit()


def print_danawa_results():
  if 'DANAWA_API_KEY_SEARCH' not in current_app.config:
    __logger__.warning('DANAWA_API_KEY_SEARCH not found')
    return
  api_key = current_app.config['DANAWA_API_KEY_SEARCH']
  heatsinks = db.session.query(Maker.name, Heatsink).join(
      Heatsink, Maker.id == Heatsink.maker_id).order_by(Maker.name, Heatsink.name)
  for maker_name, heatsink in heatsinks:
    if heatsink.danawa_id is not None:
      continue
    url = 'http://api.danawa.com/api/search/product/info'
    query = {
      'key': api_key,
      'mediatype': 'json',
      'keyword': (maker_name + ' ' + heatsink.name).encode('UTF-8'),
      'cate_c1': 862,
    }
    json_text = get_cached_response_text(url + '?' + urllib.urlencode(query))
    data = load_danawa_json(json_text)
    if data is None:
      continue
    if int(data['totalCount']) == 0:
      print u'{0} {1}: NO DATA'.format(maker_name, heatsink.name)
      continue
    if not isinstance(data['productList'], list):
      data['productList'] = [data['productList']]
    print u'{0} {1}'.format(maker_name, heatsink.name)
    for product_data in data['productList']:
      print u'  {maker} {prod_name} id={prod_id} min_price={min_price}'.format(**product_data)


def get_cached_response_text(url):
  key = base64.b64encode(url, '-_')
  html = cache.get(key)
  if html:
    return html
  resp = requests.get(url)
  html = resp.text
  # Prevent partial refreshing by setting the timeout a bit shorter.
  cache.set(key, html, timeout=current_app.config['UPDATE_INTERVAL'] - 600)
  return html


def load_danawa_json(text):
  try:
    return json.loads(text)
  except ValueError:
    if text.startswith('<?xml'):
      try:
        result = lxml.etree.fromstring(strip_xml_encoding(text))
        __logger__.warning(u'Danawa responded with an error: %s: %s',
            result.find('code').text, result.find('message').text)
      except lxml.etree.XMLSyntaxError:
        __logger__.warning(u'Danawa responded with an invalid XML')
    else:
      __logger__.warning(u'Danawa responded with an incomprehensible text')


def compress_spaces(s):
  return re.sub(r'\s+', ' ', s).strip()


def dictitemgetter(*args):
  def get(d):
    rv = tuple(d.get(i) for i in args)
    return rv if len(rv) > 2 else rv[0]
  return get


def subdict(d, *args):
  return {k: d[k] for k in args if k in d}


def warn(msg):
  if msg not in _warnings:
    __logger__.warning(msg)
    _warnings.add(msg)
_warnings = set()


def reset_warnings():
  _warnings.clear()


class ParseError(Exception):
  pass
