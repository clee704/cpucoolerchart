from __future__ import division
import sys


PY2 = sys.version_info[0] == 2
PY26 = sys.version_info < (2, 7)


if not PY2:
    text_type = str
    string_types = (str,)

    def to_bytes(x, charset=sys.getdefaultencoding(), errors='strict'):
        if x is None:
            return None
        if isinstance(x, (bytes, bytearray, memoryview)):
            return bytes(x)
        if isinstance(x, str):
            return x.encode(charset, errors)
        raise TypeError('expected bytes or str, not ' + type(x).__name__)

    def to_native(x, charset=sys.getdefaultencoding(), errors='strict'):
        if x is None or isinstance(x, str):
            return x
        return x.decode(charset, errors)

    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())

    import urllib
    import http
else:
    text_type = unicode
    string_types = (str, unicode)

    def to_bytes(x, charset=sys.getdefaultencoding(), errors='strict'):
        if x is None:
            return None
        if isinstance(x, (bytes, bytearray, buffer)):
            return bytes(x)
        if isinstance(x, unicode):
            return x.encode(charset, errors)
        raise TypeError('expected bytes or unicode, not ' + type(x).__name__)

    def to_native(x, charset=sys.getdefaultencoding(), errors='strict'):
        if x is None or isinstance(x, str):
            return x
        return x.encode(charset, errors)

    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()

    import types
    import urllib as urllib_old
    import urllib2
    import urlparse
    urllib = types.ModuleType('urllib')
    urllib.parse = types.ModuleType('urllib.parse')
    urllib.parse.urlencode = urllib_old.urlencode
    urllib.parse.urlparse = urlparse.urlparse
    urllib.request = types.ModuleType('urllib.request')
    urllib.request.urlopen = urllib2.urlopen
    urllib.request.install_opener = urllib2.install_opener
    urllib.request.build_opener = urllib2.build_opener
    urllib.request.HTTPHandler = urllib2.HTTPHandler
    urllib.response = types.ModuleType('urllib.response')
    urllib.response.addinfourl = urllib2.addinfourl
    import httplib
    http = types.ModuleType('http')
    http.client = httplib


if PY26:
    from ordereddict import OrderedDict

    def total_seconds(td):
        return (td.microseconds + (td.seconds + td.days * 24 * 3600) *
                10 ** 6) / 10 ** 6
else:
    from collections import OrderedDict

    def total_seconds(td):
        return td.total_seconds()
