# -*- coding: UTF-8 -*-
"""
    cpucoolerchart.crawler_data
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Defines rules to compensate for inconsistencies in Coolenjoy data and
    Danawa product identifiers.

    .. autodata:: MAKER_FIX
       :annotation: = {...}

    .. autodata:: MODEL_FIX
       :annotation: = {...}

    .. autodata:: INCONSISTENCY_FIX
       :annotation: = {...}

    .. autodata:: DANAWA_ID_MAPPING
       :annotation: = {...}

"""

#: Mapping that encodes rules to rewrite inconsistent maker names.
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

#: Mapping that encodes rules to rewrite inconsistent heatsink model names.
MODEL_FIX = {
    # 3Rsystem
    u'iceage 120': u'iCEAGE 120',
    u'iceage 120 boss': u'iCEAGE 120 BOSS',
    u'iceage 120 prima': u'iCEAGE 120 PRIMA',
    u'iceage 90mm': u'iCEAGE 90mm',
    # AMD
    u'amd정품': u'AMD 정품',
    # ASUS
    u'triton 79 amazing': u'TRITON 79 AMAZING',
    # CoolerMaster
    u'geminll (풍신장)∩': u'Gemin II ∩',
    u'geminll (풍신장)∪': u'Gemin II ∪',
    # Corsair
    u'hydro series h50': u'H50',
    # SilverStone
    u'sst-he01': u'Heligon HE01',
    u'he-02': u'Heligon HE02',
    u'ar01': u'Argon AR01',
    u'ar03': u'Argon AR03',
    u'td02': u'Tundra TD02',
    u'td03': u'Tundra TD03',
    # Sunbeamtech
    u'core_contact freezer 92': u'Core-Contact Freezer 92',
    # Thermalright
    u'silverarrow sb-e': u'Silver Arrow SB-E',
    u'true spirit': u'True Spirit',
    u'ultra 120': u'Ultra-120',
    u'ultra 120 extreme': u'Ultra-120 eXtreme',
    # Thermaltake
    u'bigtyp 14pro(cl-p0456)': u'BigTyp 14Pro CL-P0456',
    # ThermoLab
    u'baram(바람)': u'BARAM',
    u'baram shine(바람 샤인)': u'BARAM Shine',
    u'baram 2010': u'BARAM2010',
    # Xigmatek
    u'dark knight-s1283': u'Dark Knight S1283',
    # Zalman
    u'cnps9700nt': u'CNPS9700 NT',
    u'cnps9900led': u'CNPS9900 LED',
}

#: Mapping that encodes rules to fix inconsistent model data such as width and
#: depth.
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

#: Mapping that encodes rules to map each heatsink model to corresponding
#: Danawa product identifier.
DANAWA_ID_MAPPING = {
    u'corsair h100': 1465177,
    u'corsair h100i': 1896659,
    u'corsair h110': 2054714,
    u'corsair h40': 1591684,
    u'corsair h55': 1875650,
    u'corsair h60': 1340330,
    u'corsair new h60': 1884431,
    u'corsair h70': 1230305,
    u'corsair h80': 1443537,
    u'corsair h80i': 1896626,
    u'corsair h90': 2048037,
    u'corsair h50': 956488,
    u'thermalright hr-02 macho': 1764303,
    u'thermalright true spirit 140': 1536172,
    u'thermalright venomous x': 1764275,
    u'thermaltake big typhoon vx': 512185,
    u'thermaltake bigtyp 14pro cl-p0456': 803304,
    u'thermaltake water 2.0 extreme': 1975137,
    u'tuniq tower 120 extreme': 930715,
    u'xigmatek colosseum sm128164': 1363703,
    u'xigmatek loki sd963': 1363843,
    u'zalman cnps10x extreme': 901173,
    u'zalman cnps10x flex': 960357,
    u'zalman cnps10x optima': 1609054,
    u'zalman cnps10x performa': 1014974,
    u'zalman cnps10x quiet': 922018,
    u'zalman cnps11x performa': 1537168,
    u'zalman cnps11x': 1331101,
    u'zalman cnps12x': 1504781,
    u'zalman cnps20lq': 1573512,
    u'zalman cnps7700-cu': 43991,
    u'zalman cnps7x performa': 1350566,
    u'zalman cnps8000': 1546329,
    u'zalman cnps8700 led': 498981,
    u'zalman cnps9500 led': 586840,
    u'zalman cnps9700 led': 284022,
    u'zalman cnps9700 nt': 365992,
    u'zalman cnps9900 led': 930562,
    u'zalman cnps9900 max': 1206375,
    u'zalman cnps9900 nt': 930574,
    u'zalman reserator 3 max': 2188540,
    u'zalman zm-lq310': 1801121,
    u'zalman zm-lq315': 1801146,
    u'zalman zm-lq320': 1915454,
    u'zerotherm zt-10d premium 듀얼': 1166298,
    u'zerotherm zt-10d smart': 1266012,
    u'3rsystem iceage 120': 451918,
    u'3rsystem iceage 120 boss': 669681,
    u'3rsystem iceage 120 prima': 617634,
    u'3rsystem iceage 120 prima boss 2': 883448,
    u'3rsystem iceage 120 prima boss 2 hq': 995037,
    u'3rsystem iceage 90mm': 451922,
    u'apack cf800': 904056,
    u'apack core 92': 914793,
    u'apack nirvana nv120': 904058,
    u'apack nirvana nv120 premium': 573361,
    u'apack zerotherm fz120': 658661,
    u'asus lion square': 663980,
    u'asus silent square': 672687,
    u'asus triton 75': 837094,
    u'asus triton 79 amazing': 672680,
    u'akasa venom voodoo': 1520426,
    u'antec kühler h2o 620': 1318779,
    u'antec kühler h2o 920': 1341846,
    u'coolage ca-x120tf': 924154,
    u'coolit eco': 1055287,
    u'coolit vantage': 1166532,
    u'coolage 924 hdc': 737788,
    u'coolage 924 hdc plus': 1009082,
    u'coolermaster gemin ii ∩': 838212,
    u'coolermaster gemin ii ∪': 838212,
    u'coolermaster hyper 103': 2123386,
    u'coolermaster hyper 212 plus': 932592,
    u'coolermaster hyper 612 pwm': 1504783,
    u'coolermaster hyper 612s': 1485847,
    u'coolermaster hyper tx3': 1441296,
    u'coolermaster hyper z600': 838263,
    u'coolermaster hyper n620': 933669,
    u'coolermaster seidon 120m': 1885320,
    u'coolermaster seidon 120v': 2181109,
    u'coolermaster seidon 120xl': 1925602,
    u'coolermaster seidon 240m': 1925660,
    u'coolermaster tpc 812': 1921248,
    u'coolermaster v10': 1443541,
    u'coolermaster v6 gt': 1441266,
    u'coolermaster v8': 1443542,
    u'coolermaster vortex plus': 1441317,
    u'deepcool gamer storm assassin': 1867582,
    u'deepcool gammaxx 300': 1917527,
    u'deepcool gammaxx 400': 1917537,
    u'deepcool gammaxx s40': 2066742,
    u'deepcool ice blade pro': 1917551,
    u'deepcool neptwin': 1895632,
    u'enermax etd-t60': 1534157,
    u'enermax ets-t40-ta': 1467480,
    u'evercool hph-9525ea': 641739,
    u'evercool transformer 3': 1405997,
    u'gelid tranquillo': 1008427,
    u'intel rts2011lc liquid': 1579706,
    u'prolimatech megahalems rev.b': 954649,
    u'prolimatech super mega': 1238453,
    u'scythe orochi': 662047,
    u'silverstone argon ar01': 2049333,
    u'silverstone argon ar03': 2049376,
    u'silverstone heligon he02': 1888564,
    u'thermalright axp-140': 1324140,
    u'tuniq tower 120': 220390,
    u'silverstone heligon he01': 1836706,
    u'sunbeamtech core-contact freezer': 702120,
    u'sunbeamtech core-contact freezer 92': 910357,
    u'thermalright si-128': 363593,
    u'thermalright silver arrow sb-e': 1631443,
    u'thermalright ultima-90': 557455,
    u'thermalright ultra-120': 159794,
    u'thermalright ultra-120 extreme': 482195,
    u'thermolab bada': 932455,
    u'thermolab bada2010': 1021471,
    u'thermolab baram': 794508,
    u'thermolab baram2010': 1043344,
    u'thermolab baram shine': 962797,
    u'thermolab micro silencer': 639789,
    u'thermolab nano silencer': 820202,
    u'thermolab trinity': 1298177,
    u'xigmatek dark knight s1283': 1959996,
    u'zerotherm zt-10d smart 듀얼': 1266012,
    u'zalman cnps7000b-alcu': 43986,
    u'zalman cnps7000b-cu': 43987,
    u'청남아이티 hurricane': 967812,
    u'deepcool gamer storm lucifer': 2220113,
    u'xigmatek hdt-s1283': 576667,
}
