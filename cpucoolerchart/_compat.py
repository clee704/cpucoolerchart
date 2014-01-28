import sys

if sys.version_info < (2, 7):
    from ordereddict import OrderedDict
else:
    from collections import OrderedDict
