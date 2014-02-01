import os.path

from pytest import fixture
from cpucoolerchart._compat import to_bytes
from cpucoolerchart.app import create_app
from cpucoolerchart.extensions import db
from cpucoolerchart.models import Maker, Heatsink, FanConfig, Measurement


test_settings = {
    'CACHE_TYPE': 'simple',
    'SQLALCHEMY_DATABASE_URI': 'sqlite://'
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
    db.session.add(intel)
    db.session.add(coolermaster)
    db.session.add(intel_stock)
    db.session.add(intel_stock_92)
    db.session.add(Measurement(
        fan_config=intel_stock_92,
        noise=35,
        power=150,
        cpu_temp_delta=66.4,
    ))
    db.session.commit()


@fixture
def app():
    return create_app(test_settings)
