from cpucoolerchart import redis


def test_CompressedRedisCache():
    cache = redis.CompressedRedisCache()
    assert cache.load_object(cache.dump_object(1)) == 1
    assert cache.load_object(cache.dump_object('a')) == 'a'
    assert cache.load_object(cache.dump_object(True)) is True
    assert cache.load_object(cache.dump_object([1, 2, 3])) == [1, 2, 3]
    assert cache.load_object(cache.dump_object({'a': 1})) == {'a': 1}
