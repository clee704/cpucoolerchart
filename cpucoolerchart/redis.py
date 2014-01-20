"""
    cpucoolerchart.redis
    ~~~~~~~~~~~~~~~~~~~~

    Implements custom Redis cache.
"""

import zlib
from werkzeug.contrib.cache import RedisCache


class CompressedRedisCache(RedisCache):
    """RedisCache with data compression. Values are transparently compressed
    and decompressed when storing and fetching.
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
