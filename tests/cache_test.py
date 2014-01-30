import mock
import cpucoolerchart.cache


def test_CompressedRedisCache():
    cache = cpucoolerchart.cache.CompressedRedisCache()
    assert cache.load_object(cache.dump_object(1)) == 1
    assert cache.load_object(cache.dump_object('a')) == 'a'
    assert cache.load_object(cache.dump_object(True)) is True
    assert cache.load_object(cache.dump_object([1, 2, 3])) == [1, 2, 3]
    assert cache.load_object(cache.dump_object({'a': 1})) == {'a': 1}


def test_compressedredis():
    import redis
    redis.from_url = mock.Mock()
    config = {
        'CACHE_REDIS_URL': 'redis://user:pass@koi.redistogo.com:9977/'
    }
    cache = cpucoolerchart.cache.compressedredis(None, config, [], {})
    redis.from_url.assert_called_with(
        'redis://user:pass@koi.redistogo.com:9977/', db=None)
