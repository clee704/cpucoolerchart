from pytest import fixture
from cpucoolerchart.app import create_app


@fixture
def app():
    return create_app({'CACHE_TYPE': 'simple'})
