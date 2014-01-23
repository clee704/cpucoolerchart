"""
    cpucoolerchart.app
    ~~~~~~~~~~~~~~~~~~

    This module creates the WSGI application object.
"""

from datetime import timedelta
from functools import update_wrapper
import logging
import os

from flask import Flask, jsonify, Response, make_response, request, app
from flask.ext.cache import Cache
from flask.ext.sqlalchemy import SQLAlchemy, BaseQuery
try:
    import heroku
except ImportError:
    heroku = None


app = Flask(__name__, instance_path=os.getcwd(), instance_relative_config=True)

app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite://',
    CACHE_DEFAULT_TIMEOUT=3600 * 3,
    CACHE_KEY_PREFIX='cpucoolerchart:',
    ACCESS_CONTROL_ALLOW_ORIGIN='*',
    UPDATE_INTERVAL=86400,
    HEROKU_API_KEY=None,
    HEROKU_APP_NAME=None,
    DANAWA_API_KEY_SEARCH=None,
    DANAWA_API_KEY_PRODUCT_INFO=None,
)
app.config.from_envvar('CPUCOOLERCHART_SETTINGS', silent=True)

db = SQLAlchemy(app)

cache = Cache(app)


class Model(db.Model):
    __abstract__ = True

    def _column_names(self):
        return self.__table__.columns.keys()

    def update(self, **kwargs):
        for name in self._column_names():
            if name not in kwargs:
                continue
            current_value = getattr(self, name)
            new_value = kwargs[name]
            if current_value != new_value:
                setattr(self, name, new_value)

    def as_dict(self):
        return {k: getattr(self, k) for k in self._column_names()}

    def __repr__(self):
        values = ', '.join('{0}={1!r}'.format(k, getattr(self, k)) for k
                           in self._column_names())
        return '{model_name}({values})'.format(
            model_name=self.__mapper__.class_.__name__,
            values=values)

    class Query(BaseQuery):

        def find(self, **kwargs):
            return self.filter_by(**kwargs).scalar()

        def all_as_dict(self):
            return [obj.as_dict() for obj in self.all()]

    query_class = Query


class Maker(Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)


class Heatsink(Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    maker_id = db.Column(db.Integer, db.ForeignKey('maker.id'), nullable=False,
                         index=True)
    width = db.Column(db.Float)
    depth = db.Column(db.Float)
    height = db.Column(db.Float)
    heatsink_type = db.Column(db.String(31), nullable=False)
    weight = db.Column(db.Float)
    danawa_id = db.Column(db.Integer)
    price = db.Column(db.Integer)
    shop_count = db.Column(db.Integer)
    first_seen = db.Column(db.DateTime)
    image_url = db.Column(db.String(511))
    maker = db.relationship('Maker', backref=db.backref('heatsinks',
                            order_by=name.asc(),
                            cascade='all, delete-orphan'))

    __table_args__ = (db.UniqueConstraint('name', 'maker_id'),)


class FanConfig(Model):
    id = db.Column(db.Integer, primary_key=True)
    heatsink_id = db.Column(db.Integer, db.ForeignKey('heatsink.id'),
                            nullable=False, index=True)
    fan_size = db.Column(db.Integer, nullable=False)
    fan_thickness = db.Column(db.Integer, nullable=False)
    fan_count = db.Column(db.Integer, nullable=False)
    heatsink = db.relationship('Heatsink', backref=db.backref('fan_configs',
                               order_by=(fan_size.asc(), fan_thickness.asc(),
                                         fan_count.asc()),
                               cascade='all, delete-orphan'))

    __table_args__ = (db.UniqueConstraint('heatsink_id', 'fan_size',
                                          'fan_thickness', 'fan_count'),)


class Measurement(Model):
    id = db.Column(db.Integer, primary_key=True)
    fan_config_id = db.Column(db.Integer, db.ForeignKey('fan_config.id'),
                              nullable=False, index=True)
    noise = db.Column(db.Integer, nullable=False, index=True)
    power = db.Column(db.Integer, nullable=False, index=True)
    noise_actual_min = db.Column(db.Integer)
    noise_actual_max = db.Column(db.Integer)
    rpm_min = db.Column(db.Integer)
    rpm_max = db.Column(db.Integer)
    cpu_temp_delta = db.Column(db.Float, nullable=False, index=True)
    power_temp_delta = db.Column(db.Float, index=True)
    fan_config = db.relationship('FanConfig', backref=db.backref(
        'measurements',
        order_by=(noise.asc(), power.asc()),
        cascade='all, delete-orphan'))

    __table_args__ = (db.UniqueConstraint('fan_config_id', 'noise', 'power'),)


def crossdomain(origin=None, methods=None, headers=None,
                max_age=86400 * 30, attach_to_all=True,
                automatic_options=True):
    if origin is None:
        origin = app.config['ACCESS_CONTROL_ALLOW_ORIGIN']
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


@app.route('/makers')
@crossdomain()
@cache.cached()
def makers():
    items = Maker.query.all_as_dict()
    return jsonify(count=len(items), items=items)


@app.route('/heatsinks')
@crossdomain()
@cache.cached()
def heatsinks():
    items = Heatsink.query.all_as_dict()
    items.sort(key=lambda data: data['name'].lower())
    return jsonify(count=len(items), items=items)


@app.route('/fan-configs')
@crossdomain()
@cache.cached()
def fan_configs():
    items = FanConfig.query.all_as_dict()
    return jsonify(count=len(items), items=items)


@app.route('/measurements')
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
        return unicode(x).replace(delim, '_' if delim != '_' else '-')

    temp = []
    temp.append(delim.join(column_names))
    for row in rows:
        temp.append(delim.join(convert(x) for x in row))
    return '\n'.join(temp)


@app.route('/all')
@cache.cached()
def all():
    resp = Response(export_data(), mimetype='text/csv')
    resp.headers['Content-Disposition'] = 'filename="cooler.csv"'
    return resp


@app.route('/update', methods=['POST'])
def update():
    if not app.config.get('HEROKU_API_KEY'):
        return jsonify(msg='Heroku API key is not set')
    elif not app.config.get('HEROKU_APP_NAME'):
        return jsonify(msg='Heroku app name is not set')
    elif heroku is None:
        return jsonify(msg='heroku is not installed. '
                       'Add heroku to your requirements.txt')

    from .crawler import (is_update_needed, is_update_running,
                          set_update_running, unset_update_running,
                          update_data)
    if is_update_needed():
        if is_update_running():
            return jsonify(msg='already running')
        else:
            set_update_running()
            try:
                client = heroku.from_key(app.config['HEROKU_API_KEY'])
                herokuapp = client.apps[app.config['HEROKU_APP_NAME']]
                herokuapp.processes.add('update')
                return jsonify(msg='process started')
            except Exception:
                logger = logging.getLogger(__name__ + '.update')
                logger.exception("Couldn't start heroku process")
                unset_update_running()
                return jsonify(msg='failed'), 500
    else:
        return jsonify(msg='already up to date')
