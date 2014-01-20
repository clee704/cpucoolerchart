import os.path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import httplib
import io
import json
import urllib2

from cpucoolerchart import config, crawler, redis
from cpucoolerchart.app import app, db, Maker


def test_Config_from_envvars():
    config.os.environ = {
        'INT': '1',
        'FLOAT': '2.5',
        'TRUE': 'True',
        'FALSE': 'False',
        'ARRAY': '[a, b, c]',
        'STRING': 'foobar',
        'LOGGING.a.b.c': '1',
        'LOGGING."a.b".c': 'd',
        'LOGGING.a."b.c"': 'd',
    }
    config.Config.from_envvars()
    assert config.Config.INT == 1
    assert config.Config.FLOAT == 2.5
    assert config.Config.TRUE is True
    assert config.Config.FALSE is False
    assert config.Config.ARRAY == ['a', 'b', 'c']
    assert config.Config.STRING == 'foobar'
    assert config.Config.LOGGING['a']['b']['c'] == 1
    assert config.Config.LOGGING['a.b']['c'] == 'd'
    assert config.Config.LOGGING['a']['b.c'] == 'd'


def test_Config_setup_gmail_smtp():
    handler = config.Config.LOGGING['handlers']['mail_admins']
    config.Config.setup_gmail_smtp()
    assert handler['mailhost'] == 'localhost'
    config.Config.MAIL_TOADDRS = ['foo@bar.org']
    config.Config.GMAIL_USERNAME = 'user@gmail.com'
    config.Config.GMAIL_PASSWORD = 'letmein'
    config.Config.setup_gmail_smtp()
    assert handler['toaddrs'] == ['foo@bar.org']
    assert handler['mailhost'] == ('smtp.gmail.com', 587)
    assert handler['credentials'] == ('user@gmail.com', 'letmein')
    assert handler['secure'] == ()
    assert ('mail_admins' in
            config.Config.LOGGING['loggers']['cpucoolerchart']['handlers'])


def test_CompressedRedisCache():
    cache = redis.CompressedRedisCache()
    assert cache.load_object(cache.dump_object(1)) == 1
    assert cache.load_object(cache.dump_object('a')) == 'a'
    assert cache.load_object(cache.dump_object(True)) is True
    assert cache.load_object(cache.dump_object([1, 2, 3])) == [1, 2, 3]
    assert cache.load_object(cache.dump_object({'a': 1})) == {'a': 1}


def test_view_makers():
    db.drop_all()
    db.create_all()
    db.session.add(Maker(name='Intel'))
    db.session.commit()
    with app.test_client() as client:
        r = client.get('/makers')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data == {
            "count": 1,
            "items": [{"id": 1, "name": "Intel"}]
        }


def read_data(name):
    path = os.path.join(os.path.dirname(__file__), 'data', name)
    with open(path) as f:
        return f.read()


class MockHTTPHandler(urllib2.HTTPHandler):

    mock_urls = {
        'http://www.coolenjoy.net/cooln_db/cpucooler_charts.php?dd=3&test=3':
        (200, 'text/html', read_data('coolenjoy_dd=3_test=3.html')),
    }

    def http_open(self, req):
        url = req.get_full_url()
        try:
            status_code, mimetype, content = self.mock_urls[url]
        except KeyError:
            return urllib2.HTTPHandler.http_open(self, req)
        resp = urllib2.addinfourl(io.BytesIO(content),
                                  {'content-type': mimetype},
                                  url)
        resp.code = status_code
        resp.msg = httplib.responses[status_code]
        return resp


mock_opener = urllib2.build_opener(MockHTTPHandler)
urllib2.install_opener(mock_opener)


def test_extract_data():
    table = crawler.get_html_table(40, 150)
    data = crawler.extract_data(table, 40, 150)
    assert data[0] == {
        'maker': 'Corsair', 'model': 'H110', 'cpu_temp_delta': 51.8,
        'fan_count': 2, 'fan_size': 140, 'fan_thickness': 25,
        'heatsink_type': 'tower', 'noise': 40, 'power': 150,
        'power_temp_delta': 67.1, 'rpm_max': 999, 'rpm_min': 980
    }
    assert data[7] == {
        'maker': 'Deepcool', 'model': 'GAMER STORM ASSASSIN',
        'cpu_temp_delta': 57, 'fan_count': 2, 'fan_size': 140,
        'fan_thickness': 25, 'heatsink_type': 'tower', 'noise': 40,
        'power': 150, 'power_temp_delta': 47.8, 'rpm_max': 1012,
        'rpm_min': 998, 'depth': 154.0, 'height': 160.0, 'width': 140.0,
        'weight': 1378.0,
    }
