"""
    cpucoolerchart.cache
    ~~~~~~~~~~~~~~~~~~~~

    Implements custom caches.

"""

import zlib

import redis
from werkzeug.contrib.cache import RedisCache


class CompressedRedisCache(RedisCache):
    """:class:`werkzeug.contrib.cache.RedisCache` with data compression.
    Values are transparently compressed and decompressed when storing and
    fetching.

    To use this cache, set *CACHE_TYPE* to
    ``"cpucoolerchart.cache.compressedredis"`` when configuring the app.

    """

    def __init__(self, *args, **kwargs):
        super(CompressedRedisCache, self).__init__(*args, **kwargs)

    def dump_object(self, value):
        serialized_str = RedisCache.dump_object(self, value)
        try:
            return zlib.compress(serialized_str)
        except zlib.error:
            return serialized_str

    def load_object(self, value):
        try:
            serialized_str = zlib.decompress(value)
        except (zlib.error, TypeError):
            serialized_str = value
        return RedisCache.load_object(self, serialized_str)


def compressedredis(app, config, args, kwargs):
    """Returns a :class:`CompressedRedisCache`. Compatible with Flask-Cache.
    """
    kwargs.update(dict(
        host=config.get('CACHE_REDIS_HOST', 'localhost'),
        port=config.get('CACHE_REDIS_PORT', 6379),
    ))
    password = config.get('CACHE_REDIS_PASSWORD')
    if password:
        kwargs['password'] = password

    key_prefix = config.get('CACHE_KEY_PREFIX')
    if key_prefix:
        kwargs['key_prefix'] = key_prefix

    db_number = config.get('CACHE_REDIS_DB')
    if db_number:
        kwargs['db'] = db_number

    redis_url = config.get('CACHE_REDIS_URL')
    if redis_url:
        kwargs['host'] = redis.from_url(redis_url, db=kwargs.pop('db', None))

    return CompressedRedisCache(*args, **kwargs)
