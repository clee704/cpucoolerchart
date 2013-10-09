import logging

from flask import Blueprint, current_app, jsonify, render_template, request

from .extensions import db, cache
from .models import Maker, Heatsink, FanConfig, Measurement


__logger__ = logging.getLogger(__name__)


views = Blueprint('views', __name__, template_folder='templates')
cached_unless_debug = lambda f: cache.cached(unless=lambda: current_app.debug)(f)


@views.route('/')
@cached_unless_debug
def index():
  return render_template('index.html')


@views.route('/makers')
@cached_unless_debug
def makers():
  items = Maker.query.order_by('name').all_as_dict()
  return jsonify(count=len(items), items=items)


@views.route('/heatsinks')
@cached_unless_debug
def heatsinks():
  items = Heatsink.query.all_as_dict()
  items.sort(key=lambda data: data['name'].lower())
  return jsonify(count=len(items), items=items)


@views.route('/fan-configs')
@cached_unless_debug
def fan_configs():
  items = FanConfig.query.all_as_dict()
  return jsonify(count=len(items), items=items)


@views.route('/measurements')
@cached_unless_debug
def measurements():
  items = Measurement.query.order_by('cpu_temp_delta', 'power_temp_delta').all_as_dict()
  return jsonify(count=len(items), items=items)
