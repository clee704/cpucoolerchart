import json

from flask import Flask
import mock
from cpucoolerchart import crawler
from cpucoolerchart._compat import to_native
from cpucoolerchart.extensions import db, cache
import cpucoolerchart.views

from .conftest import app, read_data, fill_data


class TestViews(object):

    def setup(self):
        self.app = app()
        self.app.testing = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()

    def teardown(self):
        db.session.close()
        db.drop_all()
        db.get_engine(self.app).dispose()
        self.ctx.pop()

    def test_crossdomain(self):
        app = Flask('__test__')
        app.config.update({
            'ACCESS_CONTROL_ALLOW_ORIGIN': 'http://foo.bar'
        })
        client = app.test_client()

        @app.route('/', methods=('GET', 'PUT', 'OPTIONS'))
        @cpucoolerchart.views.crossdomain()
        def index():
            return 'Hello, world!'

        resp = client.get('/')
        assert resp.headers['Access-Control-Allow-Origin'] == 'http://foo.bar'

        resp = client.options('/')
        assert resp.headers['Access-Control-Allow-Origin'] == 'http://foo.bar'
        assert (sorted(resp.headers['Access-Control-Allow-Methods']
                           .split(', ')) ==
                ['GET', 'HEAD', 'OPTIONS', 'PUT'])

    def test_view_cache(self):
        r = self.client.get('/makers')
        assert r.status_code == 200
        data = json.loads(to_native(r.data))
        assert data == {"count": 0, "items": []}

        fill_data()
        r = self.client.get('/makers')
        assert r.status_code == 200
        data = json.loads(to_native(r.data))
        assert data == {"count": 0, "items": []}

        cache.clear()
        r = self.client.get('/makers')
        assert r.status_code == 200
        data = json.loads(to_native(r.data))
        assert data == {
            "count": 2,
            "items": [
                {"id": 1, "name": "Intel"},
                {"id": 2, "name": "CoolerMaster"},
            ]
        }

    def test_view_func_heatsinks(self):
        fill_data()
        r = self.client.get('/heatsinks')
        assert r.status_code == 200
        data = json.loads(to_native(r.data))
        assert data == {
            "count": 1,
            "items": [{
                "id": 1,
                "maker_id": 1,
                "name": "Stock",
                "heatsink_type": "flower",
                "width": None,
                "depth": None,
                "height": None,
                "weight": None,
                "danawa_id": None,
                "price": None,
                "shop_count": None,
                "first_seen": None,
                "image_url": None,
            }]
        }

    def test_view_func_fan_configs(self):
        fill_data()
        r = self.client.get('/fan-configs')
        assert r.status_code == 200
        data = json.loads(to_native(r.data))
        assert data == {
            "count": 1,
            "items": [{
                "id": 1,
                "heatsink_id": 1,
                "fan_count": 1,
                "fan_size": 92,
                "fan_thickness": 15,
            }]
        }

    def test_view_func_measurements(self):
        fill_data()
        r = self.client.get('/measurements')
        assert r.status_code == 200
        data = json.loads(to_native(r.data))
        assert data == {
            "count": 1,
            "items": [{
                "id": 1,
                "fan_config_id": 1,
                "noise": 35,
                "noise_actual_min": None,
                "noise_actual_max": None,
                "power": 150,
                "rpm_min": None,
                "rpm_max": None,
                "cpu_temp_delta": 66.4,
                "power_temp_delta": None,
            }]
        }

    def test_view_func_all(self):
        fill_data()
        r = self.client.get('/all')
        assert r.status_code == 200
        assert r.data + b'\n' == read_data('mock.csv')

    def test_view_func_update(self):
        heroku = cpucoolerchart.views.heroku = mock.Mock()
        heroku.from_key = mock.MagicMock()
        cpucoolerchart.views.is_update_needed = mock.Mock(return_value=True)

        self.app.config['HEROKU_API_KEY'] = '12345678'
        self.app.config['HEROKU_APP_NAME'] = 'foobar'

        r = self.client.post('/update')
        assert r.status_code == 202
        data = json.loads(to_native(r.data))
        assert data['msg'] == 'process started'
        heroku.from_key.assert_called_with('12345678')
        heroku.from_key.reset_mock()
        assert cpucoolerchart.views.is_update_running()

        r = self.client.post('/update')
        assert r.status_code == 202
        data = json.loads(to_native(r.data))
        assert data['msg'] == 'already running'
        assert heroku.from_key.call_count == 0

        crawler.unset_update_running()
        cpucoolerchart.views.is_update_needed.return_value = False
        r = self.client.post('/update')
        assert r.status_code == 202
        data = json.loads(to_native(r.data))
        assert data['msg'] == 'already up to date'
        assert heroku.from_key.call_count == 0

        cpucoolerchart.views.is_update_needed.return_value = True
        heroku.from_key.side_effect = RuntimeError
        r = self.client.post('/update')
        assert r.status_code == 500
        data = json.loads(to_native(r.data))
        assert data['msg'] == 'failed'
        assert not cpucoolerchart.views.is_update_running()
