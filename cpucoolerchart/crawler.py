"""
    cpucoolerchart.crawler
    ~~~~~~~~~~~~~~~~~~~~~~

    Implements functions for fetching and organizing data from Coolenjoy
    and Danawa.

"""

from __future__ import print_function
import base64
from datetime import datetime
import itertools
import json
import logging
import re

from flask import current_app
import lxml.etree
import lxml.html
from sqlalchemy import func

from ._compat import OrderedDict, iteritems, urllib, to_bytes
from .crawler_data import (MAKER_FIX, MODEL_FIX, INCONSISTENCY_FIX,
                           DANAWA_ID_MAPPING)
from .extensions import db, cache
from .models import Maker, Heatsink, FanConfig, Measurement


__all__ = ['NOISE_MAX', 'NOISE_LEVELS', 'CPU_POWER', 'ORDER_BY',
           'DEPENDENCIES', 'is_update_needed', 'update_data',
           'print_danawa_results']


#: Constant for maximum noise level. It does not represent an actual value.
NOISE_MAX = 100

#: List of noise levels in dB for which the measurements are taken
NOISE_LEVELS = [35, 40, 45, NOISE_MAX]

#: List of CPU power consumptions in watt for which the measurements are taken
CPU_POWER = [62, 92, 150, 200]

#: Default sorting order for measurement data
ORDER_BY = ('maker', 'model', 'fan_size', 'fan_thickness', 'fan_count',
            'noise', 'power', 'noise_actual_min')

#: Theoretical depedencies between properties to check integrity of the
#: original data. There should be, if any, very small number of violations of
#: these deps. Request corrections to Coolenjoy if you find the data
#: too inconsistent.
DEPENDENCIES = {
    # maker and model determines heatsink properties
    ('maker', 'model'): ('width', 'depth', 'height', 'heatsink_type',
                         'weight'),

    # maker, model, fan properties, noise and power determines measured values
    ('maker', 'model', 'fan_size', 'fan_thickness', 'fan_count', 'noise',
     'power'): (
        'noise_actual_min', 'noise_actual_max', 'rpm_min', 'rpm_max',
        'cpu_temp_delta', 'power_temp_delta'
    )
}


class ParseError(Exception):
    """Raised when a returned HTML page from Coolenjoy is not in a expected
    format and cannot be parsed.

    """


def _log(type, message, *args, **kwargs):
    _logger = current_app.logger
    if not logging.root.handlers and _logger.level == logging.NOTSET:
        _logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        _logger.addHandler(handler)
    getattr(_logger, type)(message, *args, **kwargs)


_warnings = set()


def warn(msg):
    """Logs a warning message if it is not seen since the last time
    :func:`reset_warnings` is called.

    """
    if msg not in _warnings:
        _log('warning', msg)
        _warnings.add(msg)


def reset_warnings():
    """Resets the warning counter used by :func:`warn`."""
    _warnings.clear()


def dictitemgetter(*args):
    """Similar to :func:`operator.itemgetter` but non-existent items are set
    to ``None``. Example:

    .. code-block:: python

        >>> dictitemgetter('a', 'b', 'c')({'a': 1, 'b': 2, 'd': 3})
        (1, 2, None)

    """
    def getter(mapping):
        rv = tuple(mapping.get(key) for key in args)
        return rv if len(rv) > 1 else rv[0]
    return getter


def heatsinks_with_maker_names():
    """Queries the database for heatsinks and its maker's name together and
    returns an iterator that yields a pair of a heatsink and its maker name.

    """
    return db.session.query(Heatsink, Maker.name).join(
        Maker, Heatsink.maker_id == Maker.id)


def get_cached_response_text(url):
    """Returns a response body fetched from the specified URL. The return value
    is cached up to ``UPDATE_INTERVAL`` minus a small fixed amount of time.

    """
    key = base64.b64encode(to_bytes(url), b'-_')
    text = cache.get(key)
    if text is None:
        resp = urllib.request.urlopen(url)
        text = resp.read()
        resp.close()
        # Prevent partial refreshing by setting the timeout a bit shorter.
        cache.set(key, text,
                  timeout=current_app.config['UPDATE_INTERVAL'] - 600)
    return text


def is_update_needed():
    """Returns ``True`` if the data is not updated recently, which means that
    it is not updated for more than ``UPDATE_INTERVAL`` seconds since the last
    update.

    """
    return not cache.get('up_to_date')


def is_update_running():
    """Returns ``True`` if an update process or thread is running.

    """
    return bool(cache.get('update_running'))


def set_update_running():
    cache.set('update_running', True, timeout=3600)


def unset_update_running():
    cache.delete('update_running')


def update_data(force=False):
    """
    Updates the database with data fetched from remote sources (Coolenjoy and
    Danawa). If *force* is ``True``, always update the database even if it is
    done recently. Note that even if *force* is used, the updated data might
    not be up-to-date since responses from remote sources are cached.

    """
    try:
        if not is_update_needed() and not force:
            _log('info', 'Recently updated; nothing to do')
        elif is_update_running():
            _log('info', 'Update is in progress in other process')
        else:
            set_update_running()
            do_update_data()
            cache.set('up_to_date', True,
                      timeout=current_app.config['UPDATE_INTERVAL'])
    except Exception:
        _log('exception', 'There was an error during updating data.')
    finally:
        unset_update_running()


def do_update_data():
    """Same as :func:`update_data` but without checking for update conditions.
    Used internally by :func:`update_data`.

    """
    fix_existing_data()
    data_list = fetch_measurement_data()
    if not data_list:
        _log('warning', 'There was an error during fetching measurement data.')
    else:
        update_measurement_data(data_list)
        update_danawa_data()
        _log('info', 'Successfully updated data from remote sources')


def fix_existing_data():
    """Fixes inconsistencies in the current database. This includes correcting
    typos in names and ensuring properties such as height and weight are the
    same for the same heatsinks.

    """
    makers = Maker.query.filter(func.lower(Maker.name).in_(MAKER_FIX.keys()))
    for maker in makers:
        maker.name = MAKER_FIX[maker.name.lower()]
    heatsinks = Heatsink.query.filter(
        func.lower(Heatsink.name).in_(MODEL_FIX.keys()))
    for heatsink in heatsinks:
        heatsink.name = MODEL_FIX[heatsink.name.lower()]
    db.session.commit()

    for heatsink, maker_name in heatsinks_with_maker_names():
        key = (maker_name + ' ' + heatsink.name).lower()
        if key in INCONSISTENCY_FIX:
            heatsink.update(**INCONSISTENCY_FIX[key])
    db.session.commit()


def fetch_measurement_data():
    """Fetches measurement data from Coolenjoy and returns a inconsistency-free
    data list. It contains information about makers, heatsinks, fan configs,
    and measurements.

    """
    reset_warnings()
    data_list = []
    for noise in NOISE_LEVELS:
        for power in CPU_POWER:
            if noise != NOISE_MAX and noise <= 40 and power >= 200:
                continue
            try:
                table = get_html_table(noise, power)
            except Exception:
                _log('warning', 'An error occurred while requesting a page',
                     exc_info=True)
                return []  # Do not return partially fetched data list
            try:
                new_data_list = extract_data(table, noise, power)
            except ParseError:
                _log('warning', 'An error occurred while parsing a page',
                     exc_info=True)
                return []  # Do not return partially fetched data list
            data_list.extend(new_data_list)
    data_list.sort(key=dictitemgetter(*ORDER_BY))
    data_list = ensure_consistency(data_list)
    return data_list


def get_html_table(noise, power):
    URL_FMT = ('http://www.coolenjoy.net/cooln_db/cpucooler_charts.php?'
               'dd={noise}&test={power}')
    noise_mapping = {35: 4, 40: 3, 45: 2, NOISE_MAX: 1}
    cpu_mapping = {62: 1, 92: 2, 150: 3, 200: 4}
    html = get_cached_response_text(URL_FMT.format(noise=noise_mapping[noise],
                                                   power=cpu_mapping[power]))
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
            data['maker'] = decode_maker(cells[0].text)
            data['model'] = decode_model(cells[0].find('br').tail)
            decode_dimension(data, cells[1].text)
            data['heatsink_type'] = decode_heatsink_type(
                cells[1].find('br').tail)
            data['weight'] = decode_weight(cells[1].find('br').tail)
            decode_fan_info(data, cells[2].text)
            decode_rpm(data, cells[2].find('br').tail)
            data['noise'] = noise
            if noise == NOISE_MAX:
                decode_noise_actual(data, cells[3].text)
            data['power'] = power
            decode_temp_info(
                data,
                cells[3 if noise != NOISE_MAX else 4].xpath('.//font'))
            fix_inconsistency(data)
            data_list.append(dict((k, data[k]) for k in data
                                  if data[k] is not None))
        except Exception:
            _log('exception', 'An error occurred while parsing a page')
            raise ParseError()
    if not data_list:
        raise ParseError('table rows not found')
    return data_list


def decode_maker(text):
    maker = re.sub(r'\s+', ' ', text).strip()
    return MAKER_FIX.get(maker.lower(), maker).replace('/', '-')


def decode_model(text):
    model = re.sub(r'\s+', ' ', text).strip()
    return MODEL_FIX.get(model.lower(), model)


def decode_dimension(data, text):
    if not text or text == '-':
        return
    m = re.search(r'([0-9.]+)\s*x\s*([0-9.]+)\s*x\s*([0-9.]+)', text, re.I)
    if not m:
        warn(u'unrecognizable dimension: {0}'.format(text))
        return
    data['width'] = float(m.group(1))
    data['depth'] = float(m.group(2))
    data['height'] = float(m.group(3))


def decode_heatsink_type(text):
    return re.sub(r'\s+', ' ', text.split('/')[0].lower()).strip()


def decode_weight(text):
    m = re.search(r'([0-9.]+)\s*g', text)
    if not m:
        warn(u'unrecognizable weight: {0}'.format(text))
        return
    weight = float(m.group(1))
    return weight if weight > 0 else None


def decode_fan_info(data, text):
    m = re.search(r'([0-9]+)(?:x([0-9]+))?/([0-9]+)T', text)
    if not m:
        warn(u'unrecognizable fan_info: {0}'.format(text))
        return
    data['fan_size'] = int(m.group(1))
    data['fan_count'] = int(m.group(2)) if m.group(2) is not None else 1
    data['fan_thickness'] = int(m.group(3))


def decode_rpm(data, text):
    m = re.search(r'(?:([0-9]+)(?:\s*-\s*([0-9]+))?)?\s*rpm', text)
    if not m:
        warn(u'unrecognizable rpm: {0}'.format(text))
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


def decode_noise_actual(data, text):
    if not text:
        return
    m = re.search(r'([0-9.]+)(?:\s*-\s*([0-9.]+))?', text)
    if not m:
        warn(u'unrecognizable noise_actual: {0}'.format(text))
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
    warn(u'interpreted unrecognizable noise_actual {0} as {1}'.format(
        text, minimum))
    data['noise_actual_max'] = minimum
    assert data['noise_actual_min'] <= data['noise_actual_max']


def decode_temp_info(data, elements):
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
        for x, y in iteritems(DEPENDENCIES):
            keys = tuple(data.get(k) for k in x)
            values = tuple(data.get(k) for k in y)
            if keys not in first_values[x]:
                first_values[x][keys] = values
            elif first_values[x][keys] != values:
                warn((u'dependency {0} -> {1} violated: {2}: {3} != {4}; '
                      u'the latter will be removed').format(
                    x, y, keys, first_values[x][keys], values))
                remove = True
        if not remove:
            new_data_list.append(data)
    return new_data_list


def update_measurement_data(data_list):
    groups = itertools.groupby(data_list, dictitemgetter('maker'))
    maker_ids = set()
    for maker_name, data_sublist in groups:
        maker_id = update_maker(data_sublist, maker_name)
        if maker_id is not None:
            maker_ids.add(maker_id)
    for maker in Maker.query.filter(~Maker.id.in_(maker_ids)):
        db.session.delete(maker)
        _log('debug', u'Deleted old maker: %s', maker.name)

    db.session.commit()


def update_maker(data_list, maker_name):
    keys = dict(name=maker_name)
    data = keys
    maker = Maker.query.find(**keys)
    if maker is None:
        maker = Maker(**data)
        db.session.add(maker)
        _log('debug', u'Added new maker: %s', maker.name)
    else:
        maker.update(**data)

    groups = itertools.groupby(data_list, dictitemgetter(
        'model', 'width', 'depth', 'height', 'heatsink_type', 'weight'))
    heatsink_ids = set()
    for heatsink_data, data_sublist in groups:
        heatsink_id = update_heatsink(data_sublist, maker, *heatsink_data)
        if heatsink_id is not None:
            heatsink_ids.add(heatsink_id)
    if maker.id is not None:
        for heatsink in Heatsink.query.filter(
                Heatsink.maker_id == maker.id).filter(
                ~Heatsink.id.in_(heatsink_ids)):
            db.session.delete(heatsink)
            _log('debug', u'Deleted old heatsink: %s', heatsink.name)

    return maker.id


def update_heatsink(data_list, maker, model_name, width, depth, height,
                    heatsink_type, weight):
    keys = dict(name=model_name, maker_id=maker.id)
    data = dict(name=model_name, maker=maker, width=width, depth=depth,
                height=height, heatsink_type=heatsink_type, weight=weight)
    heatsink = Heatsink.query.find(**keys)
    if heatsink is None:
        heatsink = Heatsink(**data)
        db.session.add(heatsink)
        _log('debug', u'Added new heatsink: %s', heatsink.name)
    else:
        heatsink.update(**data)

    groups = itertools.groupby(data_list, dictitemgetter(
        'fan_size', 'fan_thickness', 'fan_count'))
    fan_config_ids = set()
    for fan_config_data, data_sublist in groups:
        fan_config_id = update_fan_config(data_sublist, heatsink,
                                          *fan_config_data)
        if fan_config_id is not None:
            fan_config_ids.add(fan_config_id)
    if heatsink.id is not None:
        for fan_config in FanConfig.query.filter(
                FanConfig.heatsink_id == heatsink.id).filter(
                ~FanConfig.id.in_(fan_config_ids)):
            db.session.delete(fan_config)
            _log('debug', u'Deleted old fan config (id=%d)', fan_config.id)

    return heatsink.id


def update_fan_config(data_list, heatsink, fan_size, fan_thickness, fan_count):
    keys = dict(fan_size=fan_size, fan_thickness=fan_thickness,
                fan_count=fan_count, heatsink_id=heatsink.id)
    data = dict(fan_size=fan_size, fan_thickness=fan_thickness,
                fan_count=fan_count, heatsink=heatsink)
    fan_config = FanConfig.query.find(**keys)
    if fan_config is None:
        fan_config = FanConfig(**data)
        db.session.add(fan_config)
        _log('debug', u'Added new fan config')
    else:
        fan_config.update(**data)

    measurement_ids = set()
    for data in data_list:
        measurement_id = update_measurement(fan_config, data)
        if measurement_id is not None:
            measurement_ids.add(measurement_id)
    if fan_config.id is not None:
        for measurement in Measurement.query.filter(
                Measurement.fan_config_id == fan_config.id).filter(
                ~Measurement.id.in_(measurement_ids)):
            db.session.delete(measurement)
            _log('debug', u'Deleted old measurement (id=%d)', measurement.id)

    return fan_config.id


def update_measurement(fan_config, data):
    keys = dict((k, data[k]) for k in ('noise', 'power') if k in data)
    keys['fan_config_id'] = fan_config.id
    data = dict((k, data[k]) for k in ('noise', 'power', 'noise_actual_min',
                                       'noise_actual_max', 'rpm_min',
                                       'rpm_max', 'cpu_temp_delta',
                                       'power_temp_delta') if k in data)
    data['fan_config'] = fan_config
    measurement = Measurement.query.find(**keys)
    if measurement is None:
        measurement = Measurement(**data)
        db.session.add(measurement)
        _log('debug', u'Added new measurement')
    else:
        measurement.update(**data)

    return measurement.id


def update_danawa_data():
    if not current_app.config.get('DANAWA_API_KEY_PRODUCT_INFO'):
        _log('warning', 'DANAWA_API_KEY_PRODUCT_INFO not found. '
             'Price data could not be fetched.')
        return
    api_key = current_app.config['DANAWA_API_KEY_PRODUCT_INFO']
    try:
        for heatsink, maker_name in heatsinks_with_maker_names():
            key = (maker_name + ' ' + heatsink.name).lower()
            if (key in DANAWA_ID_MAPPING and
                    DANAWA_ID_MAPPING[key] != heatsink.danawa_id):
                heatsink.danawa_id = DANAWA_ID_MAPPING[key]
            if heatsink.danawa_id is None:
                continue
            url = 'http://api.danawa.com/api/main/product/info'
            query = OrderedDict([
                ('key', api_key),
                ('mediatype', 'json'),
                ('prodCode', heatsink.danawa_id),
            ])
            json_text = get_cached_response_text(url + '?' +
                                                 urllib.parse.urlencode(query))
            data = load_danawa_json(json_text)
            if data is None:
                continue
            min_price = int(data.get('minPrice', 0))
            if min_price:
                heatsink.price = min_price
            shop_count = int(data.get('shopCount', 0))
            if shop_count:
                heatsink.shop_count = shop_count
            input_date = datetime.strptime(data['inputDate'],
                                           '%Y-%m-%d %H:%M:%S')
            heatsink.first_seen = input_date
            for image_info in data['images']['image']:
                if image_info['name'] == 'large_1':
                    heatsink.image_url = image_info['url']
                    break
        db.session.commit()
    except Exception:
        _log('exception', 'An error occurred while updating danawa data')
        db.session.rollback()


def print_danawa_results():
    """Searches Danawa for heatsinks that don't have entries in
    :data:`~cpucoolerchart.crawler_data.DANAWA_ID_MAPPING` and prints results.
    It is useful to find missing Danawa identifiers for heatsinks.

    """
    if not current_app.config.get('DANAWA_API_KEY_SEARCH'):
        _log('warning', 'DANAWA_API_KEY_SEARCH not found')
        return
    api_key = current_app.config['DANAWA_API_KEY_SEARCH']
    for heatsink, maker_name in heatsinks_with_maker_names():
        if heatsink.danawa_id is not None:
            continue
        url = 'http://api.danawa.com/api/search/product/info'
        query = OrderedDict([
            ('key', api_key),
            ('mediatype', 'json'),
            ('keyword', (maker_name + ' ' + heatsink.name).encode('UTF-8')),
            ('cate_c1', 862),
        ])
        json_text = get_cached_response_text(url + '?' +
                                             urllib.parse.urlencode(query))
        data = load_danawa_json(json_text)
        if data is None:
            continue
        if int(data['totalCount']) == 0:
            print(u'{0} {1}: NO DATA'.format(maker_name, heatsink.name))
            continue
        if not isinstance(data['productList'], list):
            data['productList'] = [data['productList']]
        print(u'{0} {1}'.format(maker_name, heatsink.name))
        f = u'    {maker} {prod_name} id={prod_id} min_price={min_price}'
        for product_data in data['productList']:
            print(f.format(**product_data))


def load_danawa_json(text):
    try:
        return json.loads(text)
    except ValueError:
        if text.startswith('<?xml'):
            try:
                result = lxml.etree.fromstring(text)
                _log('warning', u'Danawa responded with an error: %s: %s',
                     result.find('code').text,
                     result.find('message').text)
            except lxml.etree.XMLSyntaxError:
                _log('warning', u'Danawa responded with an invalid XML')
        else:
            _log('warning', u'Danawa responded with an incomprehensible text')
