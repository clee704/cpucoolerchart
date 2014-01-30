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

from ._compat import text_type
from .crawler import (is_update_needed, is_update_running, set_update_running,
                      unset_update_running, update_data)
from .extensions import db, cache
from .models import Maker, Heatsink, FanConfig, Measurement


views = Blueprint('views', __name__)


def crossdomain(origin=None, methods=None, headers=None,
                max_age=86400 * 30, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if origin is not None and not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

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
    items = Maker.query.all_as_dict()
    return jsonify(count=len(items), items=items)


@views.route('/heatsinks')
@crossdomain()
@cache.cached()
def heatsinks():
    items = Heatsink.query.all_as_dict()
    items.sort(key=lambda data: data['name'].lower())
    return jsonify(count=len(items), items=items)


@views.route('/fan-configs')
@crossdomain()
@cache.cached()
def fan_configs():
    items = FanConfig.query.all_as_dict()
    return jsonify(count=len(items), items=items)


@views.route('/measurements')
@crossdomain()
@cache.cached()
def measurements():
    items = Measurement.query.all_as_dict()
    return jsonify(count=len(items), items=items)


def export_data(delim=','):
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
        Measurement.power, Measurement.noise_actual_min).all()

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
    resp = Response(export_data(), mimetype='text/csv')
    resp.headers['Content-Disposition'] = 'filename="cooler.csv"'
    return resp


@views.route('/update', methods=['POST'])
def update():
    if not current_app.config.get('HEROKU_API_KEY'):
        return jsonify(msg='Heroku API key is not set')
    elif not current_app.config.get('HEROKU_APP_NAME'):
        return jsonify(msg='Heroku app name is not set')
    elif heroku is None:
        return jsonify(msg='heroku is not installed. '
                       'Add heroku to your requirements.txt')

    if is_update_needed():
        if is_update_running():
            return jsonify(msg='already running')
        else:
            set_update_running()
            try:
                client = heroku.from_key(current_app.config['HEROKU_API_KEY'])
                herokuapp = client.apps[current_app.config['HEROKU_APP_NAME']]
                herokuapp.processes.add('update')
                return jsonify(msg='process started')
            except Exception:
                current_app.logger.exception("Couldn't start heroku process")
                unset_update_running()
                return jsonify(msg='failed'), 500
    else:
        return jsonify(msg='already up to date')
