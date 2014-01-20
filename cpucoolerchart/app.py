"""
    cpucoolerchart.app
    ~~~~~~~~~~~~~~~~~~

    This module creates the WSGI application object.
"""

import logging.config

from flask import Flask, jsonify, Response
from flask.ext.cache import Cache
from flask.ext.sqlalchemy import SQLAlchemy, BaseQuery

from .config import Config
from .redis import RedisCache, CompressedRedisCache


app = Flask(__name__)

Config.from_envvars()
Config.setup_gmail_smtp()
app.config.from_object(Config)
app.config.from_envvar('CCC_SETTINGS', silent=True)
logging.config.dictConfig(app.config['LOGGING'])

db = SQLAlchemy(app)

cache = Cache(app)
if app.config.get('CACHE_TYPE') == 'redis':
    if app.config.get('CACHE_COMPRESSION'):
        cache.cache.__class__ = CompressedRedisCache
    else:
        cache.cache.__class__ = RedisCache

# if app.config.get('GZIP'):
#     pass  # TODO


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


@app.route('/makers')
@cache.cached()
def makers():
    items = Maker.query.all_as_dict()
    return jsonify(count=len(items), items=items)


@app.route('/heatsinks')
@cache.cached()
def heatsinks():
    items = Heatsink.query.all_as_dict()
    items.sort(key=lambda data: data['name'].lower())
    return jsonify(count=len(items), items=items)


@app.route('/fan-configs')
@cache.cached()
def fan_configs():
    items = FanConfig.query.all_as_dict()
    return jsonify(count=len(items), items=items)


@app.route('/measurements')
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
