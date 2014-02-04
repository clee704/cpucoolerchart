import io
import os
from tempfile import mkstemp

from fakeredis import FakeRedis
from pytest import fixture
from rq import Queue

from cpucoolerchart._compat import to_bytes, http, urllib
from cpucoolerchart.app import create_app
from cpucoolerchart.extensions import db as flask_db
import cpucoolerchart.extensions
from cpucoolerchart.models import Maker, Heatsink, FanConfig, Measurement


redis = FakeRedis()
cpucoolerchart.extensions.redis = redis
cpucoolerchart.extensions.update_queue = Queue('update', connection=redis,
                                               default_timeout=600)

tempfile_path = mkstemp()[1]

test_settings = {
    # Couldn't use in-memory databases since rq.Worker forks child processes
    # to run enqueued jobs.
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + tempfile_path,
    'CACHE_TYPE': 'simple',
    'USE_QUEUE': True,
    'RQ_URL': 'redis://user:pass@host:6379',
}


def read_file(name):
    path = os.path.join(os.path.dirname(__file__), 'data', name)
    with open(path) as f:
        return to_bytes(f.read(), 'utf-8')


def fill_data():
    intel = Maker(name='Intel')
    coolermaster = Maker(name='CoolerMaster')
    intel_stock = Heatsink(maker=intel, name='Stock',
                           heatsink_type='flower')
    intel_stock_92 = FanConfig(heatsink=intel_stock, fan_count=1,
                               fan_size=92, fan_thickness=15)
    flask_db.session.add(intel)
    flask_db.session.add(coolermaster)
    flask_db.session.add(intel_stock)
    flask_db.session.add(intel_stock_92)
    flask_db.session.add(Measurement(
        fan_config=intel_stock_92,
        noise=35,
        power=150,
        cpu_temp_delta=66.4,
    ))
    flask_db.session.commit()


@fixture
def app():
    app = create_app(test_settings)
    return app


@fixture
def db(app, request):
    def fin():
        flask_db.drop_all()
        ctx.pop()
    request.addfinalizer(fin)

    ctx = app.app_context()
    ctx.push()
    flask_db.create_all()
    return flask_db


@fixture(scope='session', autouse=True)
def setup(request):
    def teardown():
        os.unlink(tempfile_path)
    request.addfinalizer(teardown)


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
