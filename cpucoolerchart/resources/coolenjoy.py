# -*- coding: UTF-8 -*-

# Various fixes for miscellaneous typos and inconsistencies in the original
# data. Since virtually no makers or models have names differ by only case,
# the original name is converted to lowercase for compact fix dictionaries.
MAKER_FIX = {
  '3rsystem': '3Rsystem',
  '3rsystemm': '3Rsystem',
  'deep cool': 'DEEPCOOL',
  'thermalright': 'Thermalright',
  'thermalrightm': 'Thermalright',
  'tunq': 'Tuniq',
  'akasa': 'Akasa',
  'intel': 'Intel',
  'silverstone': 'SILVERSTONE',
}

MODEL_FIX = {
  'cnps9700nt': 'CNPS9700 NT',
  'cnps9900led': 'CNPS9900 LED',
  'iceage 120': 'iCEAGE 120',
  'iceage 120 boss': 'iCEAGE 120 BOSS',
  'iceage 120 prima': 'iCEAGE 120 PRIMA',
  'iceage 90mm': 'iCEAGE 90mm',
  'triton 79 amazing': 'TRITON 79 AMAZING',
  'true spirit': 'True Spirit',
  u'amd정품': u'AMD 정품',
  'core_contact freezer 92': 'Core-Contact Freezer 92',
  'bada2010': 'BADA 2010',
  u'baram shine(바람 샤인)': u'BARAM Shine',
  u'baram(바람)': u'BARAM',
  'bigtyp 14pro(cl-p0456)': 'BigTyp 14Pro CL-P0456',
  'hydro series h50': 'H50',
}

INCONSISTENCY_FIX = {
  '3Rsystem Iceage 120': {
    'width': 125.0,   # 128 -> 125
    'depth': 100.0,   # 75 -> 100
    'height': 154.0,  # 150 -> 154
  },
  'ASUS Silent Square': {
    'width': 140.0,   # 40 -> 140
  },
  'ASUS TRITON 75': {
    'height': 115.0,  # 90 -> 115
  },
  u'THERMOLAB BARAM Shine(바람 샤인)': {
    'width': 132.0,   # 67 -> 132
    'depth': 67.0,    # 132 -> 67
  },
  u'CoolerMaster Geminll (풍신장)∪': {
    'depth': 124.0,   # 145 -> 124
  },
  'Thermalright Ultra 120': {
    'height': 160.5,  # 160 -> 160.5
  }
}
