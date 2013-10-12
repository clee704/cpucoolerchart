# -*- coding: UTF-8 -*-

# Various fixes for miscellaneous typos and inconsistencies in the original
# data. Since virtually no makers or models have names differ by only case,
# the original name is converted to lowercase for compact fix dictionaries.
MAKER_FIX = {
  u'3rsystem': u'3Rsystem',
  u'3rsystemm': u'3Rsystem',
  u'thermalright': u'Thermalright',
  u'thermalrightm': u'Thermalright',
  u'tunq': u'Tuniq',
  u'akasa': u'Akasa',
  u'intel': u'Intel',
  u'silverstone': u'SilverStone',
  u'coolage': u'CoolAge',
  u'corsair': u'Corsair',
  u'enermax': u'Enermax',
  u'thermolab': u'ThermoLab',
  u'xigmatek': u'Xigmatek',
  u'sunbeamtech': u'Sunbeamtech',
  u'scythe': u'Scythe',
  u'evercool': u'Evercool',
  u'deepcool': u'Deepcool',
  u'deep cool': u'Deepcool',
  u'cogage': u'Cogage',
  u'apack': u'Apack',
  u'zalman': u'Zalman',
  u'apachi': u'Apachi',
  u'gelid': u'Gelid',
}

MODEL_FIX = {
  u'cnps9700nt': u'CNPS9700 NT',
  u'cnps9900led': u'CNPS9900 LED',
  u'iceage 120': u'iCEAGE 120',
  u'iceage 120 boss': u'iCEAGE 120 BOSS',
  u'iceage 120 prima': u'iCEAGE 120 PRIMA',
  u'iceage 90mm': u'iCEAGE 90mm',
  u'triton 79 amazing': u'TRITON 79 AMAZING',
  u'true spirit': u'True Spirit',
  u'amd정품': u'AMD 정품',
  u'core_contact freezer 92': u'Core-Contact Freezer 92',
  u'baram shine(바람 샤인)': u'BARAM Shine',
  u'baram(바람)': u'BARAM',
  u'baram 2010': u'BARAM2010',
  u'bigtyp 14pro(cl-p0456)': u'BigTyp 14Pro CL-P0456',
  u'hydro series h50': u'H50',
  u'geminll (풍신장)∩': u'Gemin II ∩',
  u'geminll (풍신장)∪': u'Gemin II ∪',
  u'sst-he01': u'Heligon HE01',
  u'he-02': u'Heligon HE02',
  u'silverarrow sb-e': u'Silver Arrow SB-E',
  u'ultra 120': u'Ultra-120',
  u'ultra 120 extreme': u'Ultra-120 eXtreme',
  u'dark knight-s1283': u'Dark Knight S1283',
}

INCONSISTENCY_FIX = {
  u'3rsystem iceage 120': {
    'width': 125.0,   # 128 -> 125
    'depth': 100.0,   # 75 -> 100
    'height': 154.0,  # 150 -> 154
  },
  u'asus silent square': {
    'width': 140.0,   # 40 -> 140
  },
  u'asus triton 75': {
    'height': 115.0,  # 90 -> 115
  },
  u'thermolab baram shine': {
    'width': 132.0,   # 67 -> 132
    'depth': 67.0,    # 132 -> 67
  },
  u'coolermaster gemin ii ∪': {
    'depth': 124.0,   # 145 -> 124
  },
  u'thermalright ultra-120': {
    'height': 160.5,  # 160 -> 160.5
  }
}
