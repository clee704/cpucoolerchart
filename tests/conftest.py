from pytest import fixture
from cpucoolerchart.app import create_app


test_settings = {
    'CACHE_TYPE': 'simple',
    'SQLALCHEMY_DATABASE_URI': 'sqlite://'
}


@fixture
def app():
    return create_app(test_settings)
