from cpucoolerchart import cache


def test_CompressedRedisCache():
    c = cache.CompressedRedisCache()
    assert c.load_object(c.dump_object(1)) == 1
    assert c.load_object(c.dump_object('a')) == 'a'
    assert c.load_object(c.dump_object(True)) is True
    assert c.load_object(c.dump_object([1, 2, 3])) == [1, 2, 3]
    assert c.load_object(c.dump_object({'a': 1})) == {'a': 1}
