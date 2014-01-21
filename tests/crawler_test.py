import httplib
import io
import os.path
import urllib2

from cpucoolerchart import crawler


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
