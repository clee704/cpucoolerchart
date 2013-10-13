import logging
import os
import subprocess
import urlparse

from flask import Blueprint, current_app, jsonify, render_template, request, Response, abort

from .config import __project_root__
from .extensions import db, cache
from .fetch import needs_update, export_data
from .models import Maker, Heatsink, FanConfig, Measurement
from .util import heroku_scale


__logger__ = logging.getLogger(__name__)


views = Blueprint('views', __name__, template_folder='templates')
current_path = lambda: request.environ.get('RAW_URI', urlpath(request.url))
cached_unless_debug = lambda f: cache.cached(
  key_prefix=lambda: 'view:' + current_path(),
  unless=lambda: current_app.debug)(f)


@views.route('/')
@cached_unless_debug
def index():
  if current_app.config.get('HEROKU_API_KEY') and needs_update():
    heroku_scale('worker', 1)
  if '_escaped_fragment_' in request.args:
    return take_snapshot()
  else:
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


@views.route('/csv')
@cached_unless_debug
def csv():
  resp = Response(export_data(), mimetype='text/csv')
  resp.headers['Content-Disposition'] = 'filename="cooler.csv"'
  return resp


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
    __logger__.warning('Could not take a snapshot; URL_ROOT is not set.')
    return abort(500)
  return subprocess.check_output([phantomjs_bin, script, url])
