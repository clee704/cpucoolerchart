# -*- coding: UTF-8 -*-
"""
    cpucoolerchart.crawler
    ~~~~~~~~~~~~~~~~~~~~~~

    Implements functions for fetching and organizing data from Coolenjoy
    and Danawa.

"""

from __future__ import print_function
import base64
from datetime import datetime, timedelta
import itertools
import json
import logging
import re

from flask import current_app
import lxml.etree
import lxml.html
from sqlalchemy import func

from ._compat import OrderedDict, iteritems, urllib, to_bytes
from .extensions import db, cache
from .models import Maker, Heatsink, FanConfig, Measurement


# Constant for maximum noise level. It is not actually 100 dB; for real values,
# refer to noise_actual_min and noise_actual_max (may be absent).
NOISE_MAX = 100

# Noise levels and CPU power consumptions where the measurements are taken.
NOISE_LEVELS = {35: 4, 40: 3, 45: 2, NOISE_MAX: 1}
CPU_POWER = {62: 1, 92: 2, 150: 3, 200: 4}

ORDER_BY = ('maker', 'model', 'fan_size', 'fan_thickness', 'fan_count',
            'noise', 'power', 'noise_actual_min')

# Theoretical depedencies between columns to check integrity of the original
# data. There should be, if any, very small number of violations of these deps.
# Request corrections to the guy who makes the original data.
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

MAKER_FIX = {
    u'3rsystem': u'3Rsystem',
    u'3rsystemm': u'3Rsystem',
    u'thermalright': u'Thermalright',
    u'thermalrightm': u'Thermalright',
    u'tunq': u'Tuniq',
    u'akasa': u'Akasa',
    u'intel': u'Intel',
    u'silverstone': u'SilverStone',
    u'coolage': u'CoolAge',
    u'corsair': u'Corsair',
    u'enermax': u'Enermax',
    u'thermolab': u'ThermoLab',
    u'xigmatek': u'Xigmatek',
    u'sunbeamtech': u'Sunbeamtech',
    u'scythe': u'Scythe',
    u'evercool': u'Evercool',
    u'deepcool': u'Deepcool',
    u'deep cool': u'Deepcool',
    u'cogage': u'Cogage',
    u'apack': u'Apack',
    u'zalman': u'Zalman',
    u'apachi': u'Apachi',
    u'gelid': u'Gelid',
}

MODEL_FIX = {
    # 3Rsystem
    u'iceage 120': u'iCEAGE 120',
    u'iceage 120 boss': u'iCEAGE 120 BOSS',
    u'iceage 120 prima': u'iCEAGE 120 PRIMA',
    u'iceage 90mm': u'iCEAGE 90mm',
    # AMD
    u'amd정품': u'AMD 정품',
    # ASUS
    u'triton 79 amazing': u'TRITON 79 AMAZING',
    # CoolerMaster
    u'geminll (풍신장)∩': u'Gemin II ∩',
    u'geminll (풍신장)∪': u'Gemin II ∪',
    # Corsair
    u'hydro series h50': u'H50',
    # SilverStone
    u'sst-he01': u'Heligon HE01',
    u'he-02': u'Heligon HE02',
    u'ar01': u'Argon AR01',
    u'ar03': u'Argon AR03',
    u'td02': u'Tundra TD02',
    u'td03': u'Tundra TD03',
    # Sunbeamtech
    u'core_contact freezer 92': u'Core-Contact Freezer 92',
    # Thermalright
    u'silverarrow sb-e': u'Silver Arrow SB-E',
    u'true spirit': u'True Spirit',
    u'ultra 120': u'Ultra-120',
    u'ultra 120 extreme': u'Ultra-120 eXtreme',
    # Thermaltake
    u'bigtyp 14pro(cl-p0456)': u'BigTyp 14Pro CL-P0456',
    # ThermoLab
    u'baram(바람)': u'BARAM',
    u'baram shine(바람 샤인)': u'BARAM Shine',
    u'baram 2010': u'BARAM2010',
    # Xigmatek
    u'dark knight-s1283': u'Dark Knight S1283',
    # Zalman
    u'cnps9700nt': u'CNPS9700 NT',
    u'cnps9900led': u'CNPS9900 LED',
}

INCONSISTENCY_FIX = {
    u'3rsystem iceage 120': {
        'width': 125.0,   # 128 -> 125
        'depth': 100.0,   # 75 -> 100
        'height': 154.0,  # 150 -> 154
    },
    u'asus silent square': {
        'width': 140.0,   # 40 -> 140
    },
    u'asus triton 75': {
        'height': 115.0,  # 90 -> 115
    },
    u'thermolab baram shine': {
        'width': 132.0,   # 67 -> 132
        'depth': 67.0,    # 132 -> 67
    },
    u'coolermaster gemin ii ∪': {
        'depth': 124.0,   # 145 -> 124
    },
    u'thermalright ultra-120': {
        'height': 160.5,  # 160 -> 160.5
    }
}

DANAWA_ID = {
    u'corsair h100': 1465177,
    u'corsair h100i': 1896659,
    u'corsair h110': 2054714,
    u'corsair h40': 1591684,
    u'corsair h55': 1875650,
    u'corsair h60': 1340330,
    u'corsair new h60': 1884431,
    u'corsair h70': 1230305,
    u'corsair h80': 1443537,
    u'corsair h80i': 1896626,
    u'corsair h90': 2048037,
    u'corsair h50': 956488,
    u'thermalright hr-02 macho': 1764303,
    u'thermalright true spirit 140': 1536172,
    u'thermalright venomous x': 1764275,
    u'thermaltake big typhoon vx': 512185,
    u'thermaltake bigtyp 14pro cl-p0456': 803304,
    u'thermaltake water 2.0 extreme': 1975137,
    u'tuniq tower 120 extreme': 930715,
    u'xigmatek colosseum sm128164': 1363703,
    u'xigmatek loki sd963': 1363843,
    u'zalman cnps10x extreme': 901173,
    u'zalman cnps10x flex': 960357,
    u'zalman cnps10x optima': 1609054,
    u'zalman cnps10x performa': 1014974,
    u'zalman cnps10x quiet': 922018,
    u'zalman cnps11x performa': 1537168,
    u'zalman cnps11x': 1331101,
    u'zalman cnps12x': 1504781,
    u'zalman cnps20lq': 1573512,
    u'zalman cnps7700-cu': 43991,
    u'zalman cnps7x performa': 1350566,
    u'zalman cnps8000': 1546329,
    u'zalman cnps8700 led': 498981,
    u'zalman cnps9500 led': 586840,
    u'zalman cnps9700 led': 284022,
    u'zalman cnps9700 nt': 365992,
    u'zalman cnps9900 led': 930562,
    u'zalman cnps9900 max': 1206375,
    u'zalman cnps9900 nt': 930574,
    u'zalman reserator 3 max': 2188540,
    u'zalman zm-lq310': 1801121,
    u'zalman zm-lq315': 1801146,
    u'zalman zm-lq320': 1915454,
    u'zerotherm zt-10d premium 듀얼': 1166298,
    u'zerotherm zt-10d smart': 1266012,
    u'3rsystem iceage 120': 451918,
    u'3rsystem iceage 120 boss': 669681,
    u'3rsystem iceage 120 prima': 617634,
    u'3rsystem iceage 120 prima boss 2': 883448,
    u'3rsystem iceage 120 prima boss 2 hq': 995037,
    u'3rsystem iceage 90mm': 451922,
    u'apack cf800': 904056,
    u'apack core 92': 914793,
    u'apack nirvana nv120': 904058,
    u'apack nirvana nv120 premium': 573361,
    u'apack zerotherm fz120': 658661,
    u'asus lion square': 663980,
    u'asus silent square': 672687,
    u'asus triton 75': 837094,
    u'asus triton 79 amazing': 672680,
    u'akasa venom voodoo': 1520426,
    u'antec kühler h2o 620': 1318779,
    u'antec kühler h2o 920': 1341846,
    u'coolage ca-x120tf': 924154,
    u'coolit eco': 1055287,
    u'coolit vantage': 1166532,
    u'coolage 924 hdc': 737788,
    u'coolage 924 hdc plus': 1009082,
    u'coolermaster gemin ii ∩': 838212,
    u'coolermaster gemin ii ∪': 838212,
    u'coolermaster hyper 103': 2123386,
    u'coolermaster hyper 212 plus': 932592,
    u'coolermaster hyper 612 pwm': 1504783,
    u'coolermaster hyper 612s': 1485847,
    u'coolermaster hyper tx3': 1441296,
    u'coolermaster hyper z600': 838263,
    u'coolermaster hyper n620': 933669,
    u'coolermaster seidon 120m': 1885320,
    u'coolermaster seidon 120v': 2181109,
    u'coolermaster seidon 120xl': 1925602,
    u'coolermaster seidon 240m': 1925660,
    u'coolermaster tpc 812': 1921248,
    u'coolermaster v10': 1443541,
    u'coolermaster v6 gt': 1441266,
    u'coolermaster v8': 1443542,
    u'coolermaster vortex plus': 1441317,
    u'deepcool gamer storm assassin': 1867582,
    u'deepcool gammaxx 300': 1917527,
    u'deepcool gammaxx 400': 1917537,
    u'deepcool gammaxx s40': 2066742,
    u'deepcool ice blade pro': 1917551,
    u'deepcool neptwin': 1895632,
    u'enermax etd-t60': 1534157,
    u'enermax ets-t40-ta': 1467480,
    u'evercool hph-9525ea': 641739,
    u'evercool transformer 3': 1405997,
    u'gelid tranquillo': 1008427,
    u'intel rts2011lc liquid': 1579706,
    u'prolimatech megahalems rev.b': 954649,
    u'prolimatech super mega': 1238453,
    u'scythe orochi': 662047,
    u'silverstone argon ar01': 2049333,
    u'silverstone argon ar03': 2049376,
    u'silverstone heligon he02': 1888564,
    u'thermalright axp-140': 1324140,
    u'tuniq tower 120': 220390,
    u'silverstone heligon he01': 1836706,
    u'sunbeamtech core-contact freezer': 702120,
    u'sunbeamtech core-contact freezer 92': 910357,
    u'thermalright si-128': 363593,
    u'thermalright silver arrow sb-e': 1631443,
    u'thermalright ultima-90': 557455,
    u'thermalright ultra-120': 159794,
    u'thermalright ultra-120 extreme': 482195,
    u'thermolab bada': 932455,
    u'thermolab bada2010': 1021471,
    u'thermolab baram': 794508,
    u'thermolab baram2010': 1043344,
    u'thermolab baram shine': 962797,
    u'thermolab micro silencer': 639789,
    u'thermolab nano silencer': 820202,
    u'thermolab trinity': 1298177,
    u'xigmatek dark knight s1283': 1959996,
    u'zerotherm zt-10d smart 듀얼': 1266012,
    u'zalman cnps7000b-alcu': 43986,
    u'zalman cnps7000b-cu': 43987,
    u'청남아이티 hurricane': 967812,
    u'deepcool gamer storm lucifer': 2220113,
    u'xigmatek hdt-s1283': 576667,
}


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


def is_update_needed():
    last_updated = cache.get('last_updated')
    if not last_updated:
        return True
    interval = current_app.config['UPDATE_INTERVAL']
    return last_updated <= datetime.now() - timedelta(seconds=interval)


def is_update_running():
    return cache.get('update_running')


def set_update_running():
    cache.set('update_running', True, timeout=3600)


def unset_update_running():
    cache.delete('update_running')


def update_data(force=False):
    try:
        if not is_update_needed() and not force:
            _log('info', 'Recently updated; nothing to do')
        elif is_update_running():
            _log('info', 'Update is in progress in other process')
        else:
            set_update_running()
            fix_existing_data()
            data_list = fetch_measurement_data()
            if not data_list:
                _log('warning', 'There was an error during updating data.')
            else:
                update_measurement_data(data_list)
                update_danawa_data()
                cache.set('last_updated', datetime.now(),
                          timeout=current_app.config['UPDATE_INTERVAL'])
                _log('info', 'Successfully updated data from remote sources')
    finally:
        unset_update_running()


def fix_existing_data():
    makers = Maker.query.filter(func.lower(Maker.name).in_(MAKER_FIX.keys()))
    for maker in makers:
        maker.name = MAKER_FIX[maker.name.lower()]
    heatsinks = Heatsink.query.filter(
        func.lower(Heatsink.name).in_(MODEL_FIX.keys()))
    for heatsink in heatsinks:
        heatsink.name = MODEL_FIX[heatsink.name.lower()]
    for heatsink, maker_name in heatsinks_with_maker_names():
        key = (maker_name + ' ' + heatsink.name).lower()
        if key in INCONSISTENCY_FIX:
            heatsink.update(**INCONSISTENCY_FIX[key])
    db.session.commit()


def fetch_measurement_data():
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
                return []  # Do not return partially fetched data list
            data_list.extend(new_data_list)
    data_list.sort(key=dictitemgetter(*ORDER_BY))
    data_list = ensure_consistency(data_list)
    return data_list


def get_html_table(noise, power):
    URL_FMT = ('http://www.coolenjoy.net/cooln_db/cpucooler_charts.php?'
               'dd={noise}&test={power}')
    html = get_cached_response_text(URL_FMT.format(noise=NOISE_LEVELS[noise],
                                                   power=CPU_POWER[power]))
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
            data['heatsink_type'] = parse_heatsink_type(
                cells[1].find('br').tail)
            data['weight'] = parse_weight(cells[1].find('br').tail)
            parse_fan_info(data, cells[2].text)
            parse_rpm(data, cells[2].find('br').tail)
            data['noise'] = noise
            if noise == NOISE_MAX:
                parse_noise_actual(data, cells[3].text)
            data['power'] = power
            parse_temp_info(
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
    warn(u'interpreted unrecognizable noise_actual {0} as {1}'.format(
        s, minimum))
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
    keys = subdict(data, 'noise', 'power')
    keys['fan_config_id'] = fan_config.id
    data = subdict(data, 'noise', 'power', 'noise_actual_min',
                   'noise_actual_max', 'rpm_min', 'rpm_max', 'cpu_temp_delta',
                   'power_temp_delta')
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
            if key in DANAWA_ID and DANAWA_ID[key] != heatsink.danawa_id:
                heatsink.danawa_id = DANAWA_ID[key]
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


def get_cached_response_text(url):
    key = base64.b64encode(to_bytes(url), b'-_')
    html = cache.get(key)
    if html:
        return html
    f = urllib.request.urlopen(url)
    html = f.read()
    f.close()
    # Prevent partial refreshing by setting the timeout a bit shorter.
    cache.set(key, html, timeout=current_app.config['UPDATE_INTERVAL'] - 600)
    return html


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


def heatsinks_with_maker_names():
    return db.session.query(Heatsink, Maker.name).join(
        Maker, Heatsink.maker_id == Maker.id)


def compress_spaces(s):
    return re.sub(r'\s+', ' ', s).strip()


def dictitemgetter(*args):
    def get(d):
        rv = tuple(d.get(i) for i in args)
        return rv if len(rv) > 2 else rv[0]
    return get


def subdict(d, *args):
    return dict((k, d[k]) for k in args if k in d)


def warn(msg):
    if msg not in _warnings:
        _log('warning', msg)
        _warnings.add(msg)
_warnings = set()


def reset_warnings():
    _warnings.clear()


class ParseError(Exception):
    pass
