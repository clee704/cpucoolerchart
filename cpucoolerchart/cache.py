"""
    cpucoolerchart.cache
    ~~~~~~~~~~~~~~~~~~~~

    Implements custom caches.
"""

import zlib
from werkzeug.contrib.cache import RedisCache


class CompressedRedisCache(RedisCache):
    """:class:`werkzeug.contrib.cache.RedisCache` with data compression.
    Values are transparently compressed and decompressed when storing and
    fetching.

    To use this cache, set *CACHE_TYPE* to
    ``"cpucoolerchart.cache.CompressedRedisCache"`` when configuring the app.

    """

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
