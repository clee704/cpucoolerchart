# -*- coding: UTF-8 -*-
"""
    cpucoolerchart.views
    ~~~~~~~~~~~~~~~~~~~~

    Defines view functions and helpers.

"""

from datetime import timedelta
from functools import update_wrapper

from flask import (Blueprint, Response, jsonify, make_response, request,
                   current_app)
try:
    import heroku
except ImportError:
    heroku = None

from ._compat import text_type, string_types, total_seconds
from .crawler import is_update_needed, update_data
from .extensions import db, cache, update_queue
from .models import Maker, Heatsink, FanConfig, Measurement


views = Blueprint('views', __name__)


def crossdomain(origin=None, methods=None, headers=None,
                max_age=86400 * 30, attach_to_all=True,
                automatic_options=True):
    """Decorater that makes a view function compatible with cross-site HTTP
    requests by attaching ``Access-Control-*`` response headers. See
    `HTTP access control (CORS)`__ for more information.

    :param origin: allowed URIs
                   (``Access-Control-Allow-Origin`` response header).
                   If it is ``None``, the value of
                   ``ACCESS_CONTROL_ALLOW_ORIGIN`` in the current app's config
                   is used.
    :type origin: :class:`str` or :class:`collections.Iterable`
    :param methods: allowed HTTP methods
                    (``Access-Control-Allow-Methods`` response header)
    :type methods: :class:`str` or :class:`collections.Iterable`
    :param headers: allowed HTTP headers
                    (``Access-Control-Allow-Headers`` response header)
    :type headers: :class:`str` or :class:`collections.Iterable`
    :param max_age: how long the results of a preflight request can be cached
                    (``Access-Control-Max-Age`` response header)
    :type max_age: :class:`int` or :class:`datetime.timedelta`
    :param attach_to_all: If ``False``, the response is unmodified unless the
                          request method is OPTIONS.
    :type attach_to_all: :class:`bool`
    :param automatic_options: If ``True``, make a default response for
                              OPTIONS requests using
                              :meth:`Flask.make_default_options_response`.
    :type automatic_options: :class:`bool`

    __ https://developer.mozilla.org/en/docs/HTTP/Access_control_CORS

    """
    if origin is not None and not isinstance(origin, string_types):
        origin = ', '.join(origin)
    if methods is not None and not isinstance(methods, string_types):
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, string_types):
        headers = ', '.join(x.upper() for x in headers)
    if isinstance(max_age, timedelta):
        max_age = int(total_seconds(max_age))

    def get_methods():
        if methods is not None:
            return methods
        options_resp = current_app.make_default_options_response()
        return options_resp.headers['Allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers
            h['Access-Control-Allow-Origin'] = (
                origin or
                current_app.config['ACCESS_CONTROL_ALLOW_ORIGIN'])
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


@views.route('/makers')
@crossdomain()
@cache.cached()
def makers():
    """Returns all heatsink makers. CORS enabled.

    **Example request**:

    .. sourcecode:: http

       GET /makers HTTP/1.1
       Host: example.com
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {
         "count": 2,
         "items": [
           {
             "id": 1,
             "name": "CoolerMaster"
           },
           {
             "id": 2,
             "name": "Corsair"
           }
         ]
       }


    **Properties**:

    =============  ======  ====================================================
    name           type    description
    =============  ======  ====================================================
    id             number  Internal identifier for a maker
    name           string  Name of the maker
    =============  ======  ====================================================

    """
    items = Maker.query.all_as_dict()
    return jsonify(count=len(items), items=items)


@views.route('/heatsinks')
@crossdomain()
@cache.cached()
def heatsinks():
    """Returns all heatsink models. CORS enabled.

    **Example request**:

    .. sourcecode:: http

       GET /heatsinks HTTP/1.1
       Host: example.com
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {
         "count": 1,
         "items": [
           {
             "danawa_id": 1465177,
             "depth": null,
             "first_seen": "Fri, 12 Aug 2011 08:03:08 GMT",
             "heatsink_type": "tower",
             "height": null,
             "id": 46,
             "image_url": "http://img.d.com/prod_img/177/465/img/145177_1.jpg",
             "maker_id": 12,
             "name": "H100",
             "price": 184760,
             "shop_count": 5,
             "weight": null,
             "width": null
           }
         ]
       }


    **Properties**:

    =============  ======  ====================================================
    name           type    description
    =============  ======  ====================================================
    id             number  Internal identifier for a heatsink
    maker_id       number  *id* of the corresponding maker
    name           string  Name of the heatsink
    heatsink_type  string  Type of the heatsink. Currently there are two types:
                           flower and tower.
    width*         number  Width of the heatsink in mm
    depth*         number  Depth of the heatsink in mm
    height*        number  Height of the heatsink in mm
    weight*        number  Weight of the heatsink in g
    danawa_id*     number  Danawa identifier for the heatsink
    price*         number  Lowest price of the heatsink on Danawa in KRW
    shop_count*    number  Number of stores selling the heatsink on Danawa
    first_seen*    date    Time when the heatsink first appeared on Danawa
    image_url*     string  URL of the photo of the heatsink
    =============  ======  ====================================================

    """
    items = Heatsink.query.all_as_dict()
    items.sort(key=lambda data: data['name'].lower())
    return jsonify(count=len(items), items=items)


@views.route('/fan-configs')
@crossdomain()
@cache.cached()
def fan_configs():
    """Returns all fan configs, combinations of a heatsink and one or more
    fans. CORS enabled.

    **Example request**:

    .. sourcecode:: http

       GET /fan-configs HTTP/1.1
       Host: example.com
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {
         "count": 2,
         "items": [
           {
             "fan_count": 1,
             "fan_size": 120,
             "fan_thickness": 25,
             "heatsink_id": 1,
             "id": 1
           },
           {
             "fan_count": 1,
             "fan_size": 120,
             "fan_thickness": 25,
             "heatsink_id": 2,
             "id": 2
           }
         ]
       }


    **Properties**:

    ===============  ======  ==================================================
    name             type    description
    ===============  ======  ==================================================
    id               number  Internal identifier for a fan config
    heatsink_id      number  *id* of the corresponding heatsink
    fan_count        number  Number of fans. Note that all fans in a single fan
                             have the same fan size and thickness.
    fan_size         number  The diameter of a fan in mm
    fan_thickness    number  The thickness of a fan in mm
    ===============  ======  ==================================================

    """
    items = FanConfig.query.all_as_dict()
    return jsonify(count=len(items), items=items)


@views.route('/measurements')
@crossdomain()
@cache.cached()
def measurements():
    """Returns all measurement data. CORS enabled.

    **Example request**:

    .. sourcecode:: http

       GET /measurements HTTP/1.1
       Host: example.com
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {
         "count": 1,
         "items": [
           {
             "cpu_temp_delta": 50.7,
             "fan_config_id": 1,
             "id": 1,
             "noise": 35,
             "noise_actual_max": null,
             "noise_actual_min": null,
             "power": 62,
             "power_temp_delta": null,
             "rpm_max": 1010,
             "rpm_min": 1002
           }
         ]
       }


    **Properties**:

    ==================  ======  ===============================================
    name                type    description
    ==================  ======  ===============================================
    id                  number  Internal identifier for a measurement
    fan_config_id       number  *id* of the corresponding fan config
    noise               number  Target noise level in dB.
                                All values are literal but a value of 100 means
                                the maximum noise level that the fan config can
                                get. In this case you may look
                                *noise_actual_min* and *noise_actual_max* for
                                the range of actual values, although these
                                values can be missing even *noise* is 100.
    noise_actual_min*   number  The minimum measured value of the actual noise
                                level in dB
    noise_actual_max*   number  The maximum measured value of the actual noise
                                level in dB
    power               number  Target CPU power consumption in watt.
    rpm_min*            number  The minimum measured value of RPM of fans
    rpm_max*            number  The maximum measured value of RPM of fans
    cpu_temp_delta      number  CPU temperature in °C
    power_temp_delta*   number  Power temperature in °C
    ==================  ======  ===============================================

    """
    items = Measurement.query.all_as_dict()
    return jsonify(count=len(items), items=items)


def export_data(delim=','):
    """Returns all data in CSV format."""
    columns = [
        Maker.name, Heatsink.name, Heatsink.width, Heatsink.depth,
        Heatsink.height, Heatsink.heatsink_type, Heatsink.weight,
        Heatsink.price, Heatsink.shop_count, Heatsink.first_seen,
        FanConfig.fan_size, FanConfig.fan_thickness, FanConfig.fan_count,
        Measurement.noise, Measurement.noise_actual_min,
        Measurement.noise_actual_max, Measurement.rpm_min, Measurement.rpm_max,
        Measurement.power, Measurement.cpu_temp_delta,
        Measurement.power_temp_delta
    ]
    column_names = [
        'maker', 'model', 'width', 'depth', 'height', 'heatsink_type',
        'weight', 'price', 'shop_count', 'first_seen', 'fan_size',
        'fan_thickness', 'fan_count', 'noise', 'noise_actual_min',
        'noise_actual_max', 'rpm_min', 'rpm_max', 'power', 'cpu_temp_delta',
        'power_temp_delta',
    ]
    rows = db.session.query(*columns).select_from(Measurement).join(
        FanConfig, FanConfig.id == Measurement.fan_config_id).join(
        Heatsink, Heatsink.id == FanConfig.heatsink_id).join(
        Maker, Maker.id == Heatsink.maker_id).order_by(
        Maker.name, Heatsink.name, FanConfig.fan_size,
        FanConfig.fan_thickness, FanConfig.fan_count, Measurement.noise,
        Measurement.power, Measurement.noise_actual_min)

    def convert(x):
        if x is None:
            return ''
        return text_type(x).replace(delim, '_' if delim != '_' else '-')

    temp = []
    temp.append(delim.join(column_names))
    for row in rows:
        temp.append(delim.join(convert(x) for x in row))
    return '\n'.join(temp)


@views.route('/all')
@cache.cached()
def all():
    """Returns all data in CSV format.

    **Example request**:

    .. sourcecode:: http

       GET /all HTTP/1.1
       Host: example.com
       Accept: */*

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Disposition: filename="cooler.csv"
       Content-Type: text/csv; charset=utf-8

       maker,model,width,depth,height,heatsink_type,weight,price,shop_count,first_seen,fan_size,fan_thickness,fan_count,noise,noise_actual_min,noise_actual_max,rpm_min,rpm_max,power,cpu_temp_delta,power_temp_delta
       3Rsystem,iCEAGE 120,125.0,100.0,154.0,tower,590.0,,,2007-04-04 16:18:55,120,25,1,35,,,1002,1010,62,50.7,
       Zalman,ZM-LQ320,,,,tower,195.0,91000,244,2013-01-31 16:57:18,120,25,2,100,58,58,2042,2068,200,60.8,64.5

    """
    resp = Response(export_data(), mimetype='text/csv')
    resp.headers['Content-Disposition'] = 'filename="cooler.csv"'
    return resp


@views.route('/update', methods=['POST'])
def update():
    """Enqueues an update job so that a worker process update the database.
    This feature is enabled when ``USE_QUEUE`` is ``True``. To process enqueued
    jobs, run a worker process (``cpucoolerchart runworker``).

    There is a special feature that starts a worker process to reduce the
    server cost. Only Heroku is supported for now. Set ``START_WORKER_NODE``
    to ``"heroku"`` and ``HEROKU_API_KEY`` and ``HEROKU_APP_NAME`` to your
    Heroku API key and app name respectively.

    To prevent DDoS attacks, it cannot be requested more frequently than once
    per 5 minutes when ``app.debug`` is ``False``.

    **Example request**:

    .. sourcecode:: http

       POST /update HTTP/1.1
       Host: example.com
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 202 OK
       Content-Type: application/json

       {
         "msg": "process started"
       }

    It returns a JSON object containing a message in the *msg* property.
    Possible messages are:

    +------------------------+------------------------------------------------+
    | message                | description                                    |
    +========================+================================================+
    | process started        | An update job is enqueued and a worker process |
    |                        | has started                                    |
    +------------------------+------------------------------------------------+
    | too many requests      | There was a request within the last 5 minutes  |
    +------------------------+------------------------------------------------+
    | already up to date     | data is already up to date                     |
    +------------------------+------------------------------------------------+
    | invalid worker type    | worker type is other than ``"heroku"``         |
    +------------------------+------------------------------------------------+
    | Heroku API key is not  | ``HEROKU_API_KEY`` is not set in config        |
    | set                    |                                                |
    +------------------------+------------------------------------------------+
    | Heroku app name is not | ``HEROKU_APP_NAME`` is not set in config       |
    | set                    |                                                |
    +------------------------+------------------------------------------------+
    | heroku is not          | :mod:`heroku` Python module is not installed   |
    | installed. Add heroku  | on your dyno.                                  |
    | to your                |                                                |
    | requirements.txt       |                                                |
    +------------------------+------------------------------------------------+
    | failed to enqueue a    | an error occurred during enqueuing a job       |
    | job                    |                                                |
    +------------------------+------------------------------------------------+
    | failed to start a      | an error occurred during starting a worker     |
    | worker                 |                                                |
    +------------------------+------------------------------------------------+

    :status 202: an update job is enqueued and a worker process has started
    :status 404: the app is not configured to update data via HTTP
    :status 429: there was a request within the last 5 minutes
    :status 500: an error occurred during enqueuing a job or starting a worker
    :status 503: worker settings are not valid

    """
    if not current_app.config.get('USE_QUEUE'):
        return jsonify(
            msg='the app is not configured to update data via HTTP'), 404

    if not current_app.debug:
        if cache.get('prevent_further_requests'):
            return jsonify(msg='too many requests'), 429
        cache.set('prevent_further_requests', True, timeout=300)

    if not is_update_needed():
        return jsonify(msg='already up to date'), 202

    try:
        update_queue.enqueue_call(update_data, result_ttl=0)
    except Exception:
        current_app.logger.exception('An error occurred during enqueuing')
        return jsonify(msg='failed to enqueue a job'), 500

    worker_type = current_app.config.get('START_WORKER_NODE')
    if not worker_type:
        return jsonify(msg='process started'), 202

    if worker_type != 'heroku':
        return jsonify(msg='invalid worker type'), 503

    if not current_app.config.get('HEROKU_API_KEY'):
        return jsonify(msg='Heroku API key is not set'), 503
    elif not current_app.config.get('HEROKU_APP_NAME'):
        return jsonify(msg='Heroku app name is not set'), 503
    elif heroku is None:
        return jsonify(msg='heroku is not installed. '
                       'Add heroku to your requirements.txt'), 503

    try:
        client = heroku.from_key(current_app.config['HEROKU_API_KEY'])
        herokuapp = client.apps[current_app.config['HEROKU_APP_NAME']]
        herokuapp.processes.add(current_app.config['HEROKU_WORKER_NAME'])
        return jsonify(msg='process started'), 202
    except Exception:
        current_app.logger.exception("Couldn't start heroku process")
        return jsonify(msg='failed to start a worker'), 500
