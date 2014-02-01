import io

from cpucoolerchart import crawler
from cpucoolerchart._compat import http, urllib
from cpucoolerchart.extensions import db
from cpucoolerchart.models import Maker, Heatsink, FanConfig, Measurement

from .conftest import read_file


class MockHTTPHandler(urllib.request.HTTPHandler):

    mock_urls = {}

    for dd in (1, 2, 3, 4):
        for test in (1, 2, 3, 4):
            if dd >= 3 and test == 4:
                continue
            key = ('http://www.coolenjoy.net/cooln_db/cpucooler_charts.php?'
                   'dd={dd}&test={test}').format(dd=dd, test=test)
            filename = 'coolenjoy_dd={dd}_test={test}.html'.format(dd=dd,
                                                                   test=test)
            mock_urls[key] = (200, 'text/html', filename)

    def http_open(self, req):
        url = req.get_full_url()
        try:
            status_code, mimetype, filename = self.mock_urls[url]
        except KeyError:
            return urllib.request.HTTPHandler.http_open(self, req)
        content = read_file(filename)
        resp = urllib.response.addinfourl(io.BytesIO(content),
                                          {'content-type': mimetype},
                                          url)
        resp.code = status_code
        resp.msg = http.client.responses[status_code]
        return resp


mock_opener = urllib.request.build_opener(MockHTTPHandler)
urllib.request.install_opener(mock_opener)


def test_dictitemgetter():
    assert crawler.dictitemgetter('a', 'b', 'c')({
        'a': 1, 'b': 2, 'd': 3
    }) == (1, 2, None)


def test_fix_existing_data(app):
    with app.app_context():
        db.create_all()
        thermalright = Maker(name='ThermalRightm')
        silverstone = Maker(name='Silverstone')
        ultra_120 = Heatsink(maker=thermalright, name='Ultra 120',
                             heatsink_type='tower', height=160)
        he01 = Heatsink(maker=silverstone, name='SST-HE01',
                        heatsink_type='tower')
        db.session.add(thermalright)
        db.session.add(silverstone)
        db.session.add(ultra_120)
        db.session.add(he01)
        db.session.commit()
        crawler.fix_existing_data()
        assert thermalright.name == 'Thermalright'
        assert silverstone.name == 'SilverStone'
        assert ultra_120.name == 'Ultra-120'
        assert ultra_120.height == 160.5
        assert he01.name == 'Heligon HE01'


def test_fetch_measurement_data(app):
    with app.app_context():
        db.create_all()
        data_list = crawler.fetch_measurement_data()
        assert data_list[0] == {
            'maker': '3Rsystem',
            'model': 'iCEAGE 120',
            'weight': 590.0,
            'width': 125.0,
            'depth': 100.0,
            'height': 154.0,
            'heatsink_type': 'tower',
            'fan_size': 120,
            'fan_thickness': 25,
            'fan_count': 1,
            'noise': 35,
            'power': 62,
            'rpm_min': 1002,
            'rpm_max': 1010,
            'cpu_temp_delta': 50.7,
        }
        assert data_list[1] == {
            'maker': '3Rsystem',
            'model': 'iCEAGE 120',
            'weight': 590.0,
            'width': 125.0,
            'depth': 100.0,
            'height': 154.0,
            'heatsink_type': 'tower',
            'fan_size': 120,
            'fan_thickness': 25,
            'fan_count': 1,
            'noise': 35,
            'power': 92,
            'rpm_min': 1002,
            'rpm_max': 1010,
            'cpu_temp_delta': 58.1,
        }


def test_update_measurement_data(app):
    with app.app_context():
        db.create_all()
        crawler.update_measurement_data([{
            'maker': 'Intel',
            'model': 'Stock',
            'heatsink_type': 'tower',
            'fan_size': 92,
            'fan_thickness': 20,
            'fan_count': 1,
            'noise': 35,
            'power': 62,
            'cpu_temp_delta': 50,
        }])
        assert Maker.query.all() == [
            Maker(id=1, name='Intel'),
        ]
        assert Heatsink.query.all() == [
            Heatsink(id=1, name='Stock', maker_id=1, heatsink_type='tower'),
        ]
        assert FanConfig.query.all() == [
            FanConfig(id=1, heatsink_id=1, fan_size=92, fan_thickness=20,
                      fan_count=1),
        ]
        assert Measurement.query.all() == [
            Measurement(id=1, fan_config_id=1, noise=35, power=62,
                        cpu_temp_delta=50),
        ]

        crawler.update_measurement_data([{
            'maker': 'Intel',
            'model': 'Stock',
            'heatsink_type': 'tower',
            'fan_size': 92,
            'fan_thickness': 20,
            'fan_count': 1,
            'noise': 35,
            'power': 62,
            'cpu_temp_delta': 51.2,
        }, {
            'maker': 'Intel',
            'model': 'Stock',
            'heatsink_type': 'tower',
            'fan_size': 92,
            'fan_thickness': 20,
            'fan_count': 1,
            'noise': 35,
            'power': 92,
            'cpu_temp_delta': 61.5,
        }, {
            'maker': 'Corsair',
            'model': 'H110',
            'heatsink_type': 'tower',
            'fan_size': 120,
            'fan_thickness': 25,
            'fan_count': 2,
            'noise': 40,
            'power': 150,
            'cpu_temp_delta': 44.1,
            'power_temp_delta': 66,
        }])
        assert Maker.query.all() == [
            Maker(id=1, name='Intel'),
            Maker(id=2, name='Corsair'),
        ]
        assert Heatsink.query.all() == [
            Heatsink(id=1, name='Stock', maker_id=1, heatsink_type='tower'),
            Heatsink(id=2, name='H110', maker_id=2, heatsink_type='tower'),
        ]
        assert FanConfig.query.all() == [
            FanConfig(id=1, heatsink_id=1, fan_size=92, fan_thickness=20,
                      fan_count=1),
            FanConfig(id=2, heatsink_id=2, fan_size=120, fan_thickness=25,
                      fan_count=2),
        ]
        assert Measurement.query.all() == [
            Measurement(id=1, fan_config_id=1, noise=35, power=62,
                        cpu_temp_delta=51.2),
            Measurement(id=2, fan_config_id=1, noise=35, power=92,
                        cpu_temp_delta=61.5),
            Measurement(id=3, fan_config_id=2, noise=40, power=150,
                        cpu_temp_delta=44.1, power_temp_delta=66),
        ]


def test_extract_data(app):
    with app.app_context():
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
