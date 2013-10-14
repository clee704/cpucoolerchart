(function () {
'use strict';

if (jQuery('html').hasClass('lt-ie8')) return;

angular.module('cpucoolerchart.controllers', [])

  .controller('DataCtrl', function ($scope, $http, $q, $location, $window, $timeout,
                                    QUERY_DELIMETER, QUERY_ARRAY_DELIMETER) {

    $scope.noiseOptions = [
      {name: '35dB', value: 35},
      {name: '40dB', value: 40},
      {name: '45dB', value: 45},
      {name: '최대', value: 100}
    ];

    $scope.powerOptions = [
      {name: '62W', value: 62},
      {name: '92W', value: 92},
      {name: '150W', value: 150},
      {name: '200W', value: 200}
    ];

    $scope.sortOptions = [
      {name: 'CPU 온도', value: 'cpu_temp_delta', alias: 'cpu'},
      {name: '전원부 온도', value: 'power_temp_delta', alias: 'power'},
      {name: '가격', value: 'price', alias: 'price'},
      {name: '높이', value: 'height', alias: 'height'},
      {name: '무게', value: 'weight', alias: 'weight'},
      {name: '소음', value: 'noise_avg', alias: 'noise'}
    ];

    $scope.heatsinkTypeOptions = [
      {name: '타워', value: 'tower'},
      {name: '플라워', value: 'flower'}
    ];

    $scope.ppOptions = [
      {name: '아주 좋음', value: 'best'},
      {name: '좋음', value: 'good'}
    ];

    $scope.g = {
      priceMin: null,
      priceMax: null,
      heightMin: null,
      heightMax: null,
      weightMin: null,
      weightMax: null,
      heatsinkType: null,
      pricePerformance: null,
      numSelectedHeatsinks: 0,
      modal: {}
    };
    $scope.loading = {};

    $scope.toggleSelection = function (heatsink, bypassProtection) {
      if ($scope.g.showSelectedOnly && !bypassProtection) return;
      heatsink.selected = !heatsink.selected;
      if (heatsink.selected) {
        $scope.g.numSelectedHeatsinks += 1;
        privateScope.selectedHeatsinks[heatsink.id] = heatsink;
      } else {
        $scope.g.numSelectedHeatsinks -= 1;
        delete privateScope.selectedHeatsinks[heatsink.id];
      }
    };

    $scope.clearSelection = function () {
      var selected = privateScope.selectedHeatsinks;
      for (var id in selected) {
        if (!selected.hasOwnProperty(id)) continue;
        selected[id].selected = false;
        delete selected[id];
      }
      $scope.g.numSelectedHeatsinks = 0;
    };

    function indexBy(arr, value) {
      var map = {};
      for (var i = 0; i < arr.length; i++) {
        map[arr[i][value]] = arr[i];
      }
      return map;
    }

    function parseNumber(x, defaultValue) {
      if (x === null || x === undefined || x === '') {
        return (defaultValue === undefined ? null : defaultValue);
      }
      x = Number(x);
      return x === null || isNaN(x) ? (defaultValue === undefined ? null : defaultValue) : x;
    }

    function getResources(url, name) {
      $scope.loading[name] = true;
      return $http.get(url).success(function (data) {
        privateScope[name] = data.items;
        privateScope[name + 'ById'] = indexBy(data.items, 'id');
        $scope.loading[name] = false;
      }).error(function () {
        $scope.error = '데이터를 가져오는 동안 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.';
        $scope.loading[name] = false;
      });
    }

    function attachProperties() {
      var empty = '-';
      for (var j = 0; j < privateScope.heatsinks.length; j++) {
        var heatsink = privateScope.heatsinks[j];
        heatsink.maker = privateScope.makersById[heatsink.maker_id];
        heatsink.size = [
          Math.round(heatsink.width) || empty,
          Math.round(heatsink.depth) || empty,
          Math.round(heatsink.height) || empty
        ].join('x');
        if (heatsink.size === [empty, empty, empty].join('x')) heatsink.size = empty;
        heatsink.weight_formatted = heatsink.weight === null ? empty :
            Math.round(heatsink.weight) + ' g';
        if (heatsink.danawa_id) {
          heatsink.danawa_url = 'http://prod.danawa.com/info?pcode=' + heatsink.danawa_id;
        }
        if (heatsink.first_seen) {
          heatsink.first_seen_timestamp = Date.parse(heatsink.first_seen);
        }
      }
      for (var i = 0; i < privateScope.measurements.length; i++) {
        var m = privateScope.measurements[i];
        m.fan_config = privateScope.fanConfigsById[m.fan_config_id];
        m.heatsink = privateScope.heatsinksById[m.fan_config.heatsink_id];
        m.maker = privateScope.makersById[m.heatsink.maker_id];
        m.heatsink_size = m.heatsink.size;
        m.heatsink_weight = m.heatsink.weight_formatted;
        m.fan_size = m.fan_config.fan_size + '/' +
            m.fan_config.fan_thickness + 'T' +
            ' x' + m.fan_config.fan_count;
        m.rpm_avg = m.rpm_min === null ? empty : Math.round((m.rpm_min + m.rpm_max) / 2) + ' rpm';
        if (m.power_temp_delta === null) m.power_temp_delta = empty;
        m.noise_avg = m.noise_actual_min === null ? empty :
            (Math.round((m.noise_actual_min + m.noise_actual_max) / 2 * 10) / 10);
        m.price_formatted = m.heatsink.price ? (m.heatsink.price / 10000).toFixed(1) : empty;
        m.danawa_url = m.heatsink.danawa_url;
        m.price = m.heatsink.price === null ? null : m.heatsink.price / 10000;
        m.height = m.heatsink.height === null ? 0 : m.heatsink.height;
        m.weight = m.heatsink.weight === null ? 0 : m.heatsink.weight;
      }
    }

    var sortMeasurements = (function () {
      var compareNumbers = function (a, b, key) {
        var x = parseNumber(a[key]),
            y = parseNumber(b[key]);
        if (x === y) return 0;
        else if (x === null) return 1;
        else if (y === null) return -1;
        else if (x < y) return -1;
        else if (x > y) return 1;
        else return 0;
      };
      return function () {
        var key = $scope.g.sortOption.value;
        if ($scope.measurements.sortKey === key) return;
        $scope.measurements.items.sort(function (a, b) {
          var c;
          if ((c = compareNumbers(a, b, key)) !== 0) return c;
          if ((c = compareNumbers(a, b, 'cpu_temp_delta')) !== 0) return c;
          if ((c = compareNumbers(a, b, 'power_temp_delta')) !== 0) return c;
          if ((c = compareNumbers(a, b, 'price')) !== 0) return c;
          return 0;
        });
        $scope.measurements.sortKey = key;
      };
    })();

    function updateMeasurementsVisibility() {
      var g = $scope.g,
          current = $scope.measurements.items,
          found = false,
          length = 0;
      if (g.pricePerformance) calculatePricePerformance();
      for (var i = 0; i < current.length; i++) {
        var m = current[i];
        m.visible = (!g.filterByMaker || m.maker.selected) &&
            (g.priceMin === null || m.price !== null && g.priceMin <= m.price) &&
            (g.priceMax === null || m.price !== null && g.priceMax >= m.price) &&
            (g.heightMin === null || m.height !== null && g.heightMin <= m.height) &&
            (g.heightMax === null || m.height !== null && g.heightMax >= m.height) &&
            (g.weightMin === null || m.weight !== null && g.weightMin <= m.weight) &&
            (g.weightMax === null || m.weight !== null && g.weightMax >= m.weight) &&
            (g.heatsinkType === null || g.heatsinkType === m.heatsink.heatsink_type) &&
            (!g.showSelectedOnly || m.heatsink.selected) &&
            (!g.pricePerformance || m.good_performance && m.good_price);
        m.first = !found && m.visible;
        if (m.first) found = true;
        if (m.visible) length += 1;
      }
      $scope.measurements.length = length;
    }

    function calculatePricePerformance() {
      var g = $scope.g,
          current = $scope.measurements.items,
          i, m;
      var thresholds = {
            best: {price: 0.5, temp: 1, tempRatio: 10, priceRatio: 6},
            good: {price: 1, temp: 2, tempRatio: 15, priceRatio: 9}
          },
          lastPrice, lastCpuTemp;
      // Pass 1: ascend CPU temp from low to high
      var orderedByCpuTemp = current.slice(0);
      orderedByCpuTemp.sort(function (a, b) { return a.cpu_temp_delta - b.cpu_temp_delta; });
      lastPrice = null;
      lastCpuTemp = null;
      for (i = 0; i < orderedByCpuTemp.length; i++) {
        m = orderedByCpuTemp[i];
        if (!m.price) continue;
        var best = false,
            refPoint = false;
        if (lastPrice === null) {
          best = true;
          refPoint = true;
        } else if (m.price < lastPrice) {
          var ratio = thresholds[g.pricePerformance].tempRatio;
          best = (m.cpu_temp_delta - lastCpuTemp) / (lastPrice - m.price) < ratio;
          refPoint = true;
        } else {
          var x = m.price - lastPrice,
              y = m.cpu_temp_delta - lastCpuTemp,
              priceLimit = thresholds[g.pricePerformance].price,
              tempLimit = thresholds[g.pricePerformance].temp;
          best = (x * x) / (priceLimit * priceLimit) + (y * y) / (tempLimit * tempLimit) < 1;
          refPoint = false;
        }
        if (best) {
          m.good_performance = true;
          if (refPoint) {
            lastPrice = m.price;
            lastCpuTemp = m.cpu_temp_delta;
          }
        } else {
          m.good_performance = false;
        }
      }
      // Pass 2: ascend price from low to high
      var orderedByPrice = current.slice(0);
      orderedByPrice.sort(function (a, b) { return a.price - b.price; });
      lastPrice = null;
      lastCpuTemp = null;
      for (i = 0; i < orderedByPrice.length; i++) {
        m = orderedByPrice[i];
        if (!m.price) continue;
        var best = false,
            refPoint = false;
        if (lastCpuTemp === null) {
          best = true;
          refPoint = true;
        } else if (m.cpu_temp_delta < lastCpuTemp) {
          var ratio = thresholds[g.pricePerformance].priceRatio;
          best = (m.price - lastPrice) / (lastCpuTemp - m.cpu_temp_delta) < ratio;
          refPoint = true;
        } else {
          var x = m.price - lastPrice,
              y = m.cpu_temp_delta - lastCpuTemp,
              priceLimit = thresholds[g.pricePerformance].price,
              tempLimit = thresholds[g.pricePerformance].temp;
          best = (x * x) / (priceLimit * priceLimit) + (y * y) / (tempLimit * tempLimit) < 1;
          refPoint = false;
        }
        if (best) {
          m.good_price = true;
          if (refPoint) {
            lastPrice = m.price;
            lastCpuTemp = m.cpu_temp_delta;
          }
        } else {
          m.good_price = false;
        }
      }
    }

    var selectMeasurements = (function () {
      var cachedMeasurementSelections = {35: {}, 40: {}, 45: {}, 100: {}};
      return function () {
        var noise = $scope.g.noise,
            power = $scope.g.power;
        var cached = cachedMeasurementSelections[noise][power];
        if (cached) {
          $scope.measurements = cached;
        } else {
          var current = [];
          for (var i = 0; i < privateScope.measurements.length; i++) {
            var m = privateScope.measurements[i];
            if (m.noise === noise && m.power === power) current.push(m);
          }
          $scope.measurements = cachedMeasurementSelections[noise][power] = {
            sortKey: 'cpu_temp_delta',
            items: current
          };
        }
        sortMeasurements();
        updateMeasurementsVisibility();
      };
    })();

    var readPath = (function () {
      function deserialize(str) {
        var obj = {},
            args = str.split(QUERY_DELIMETER);
        for (var i = 0; i < args.length; i++) {
          var x = args[i].split('='),
              name = x[0],
              value = x[1];
          obj[name] = value;
        }
        return obj;
      }
      return function () {
        var query = deserialize($location.path().substr(1)),
            values, i;
        $scope.g.noise = parseNumber(query.noise, defaultValues.noise);
        $scope.g.power = parseNumber(query.power, defaultValues.power);
        $scope.g.sortOption = privateScope.sortOptionsByAlias[query.sort] ||
            privateScope.sortOptionsByAlias[defaultValues.sort];
        $scope.g.filterByMaker = false;
        $scope.makers.forEach(function (maker) { maker.selected = false; });
        if (query.maker) {
          var makerIds = query.maker.split(QUERY_ARRAY_DELIMETER),
              filtered = false;
          for (i = 0; i < makerIds.length; i++) {
            var makerId = makerIds[i],
                maker = privateScope.makersById[makerId];
            if (!maker) continue;
            maker.selected = true;
            filtered = true;
          }
          $scope.g.filterByMaker = filtered;
        }
        if (query.price) {
          values = query.price.split('~');
          $scope.g.priceMin = parseNumber(values[0]);
          $scope.g.priceMax = parseNumber(values[1]);
        } else {
          $scope.g.priceMin = $scope.g.priceMax = null;
        }
        if (query.height) {
          values = query.height.split('~');
          $scope.g.heightMin = parseNumber(values[0]);
          $scope.g.heightMax = parseNumber(values[1]);
        } else {
          $scope.g.heightMin = $scope.g.heightMax = null;
        }
        if (query.weight) {
          values = query.weight.split('~');
          $scope.g.weightMin = parseNumber(values[0]);
          $scope.g.weightMax = parseNumber(values[1]);
        } else {
          $scope.g.weightMin = $scope.g.weightMax = null;
        }
        if (privateScope.heatsinkTypeOptionsByValue[query.type]) {
          $scope.g.heatsinkType = query.type;
        } else {
          $scope.g.heatsinkType = null;
        }
        if (query.show && query.show === 'selection') {
          $scope.g.showSelectedOnly = true;
        } else {
          $scope.g.showSelectedOnly = false;
        }
        $scope.clearSelection();
        if (query.select) {
          var heatsinkIds = query.select.split(QUERY_ARRAY_DELIMETER);
          for (i = 0; i < heatsinkIds.length; i++) {
            var heatsinkId = parseNumber(heatsinkIds[i]),
                heatsink = privateScope.heatsinksById[heatsinkId];
            if (!heatsink) continue;
            $scope.toggleSelection(heatsink, true);
          }
        }
        if (query.info && privateScope.heatsinksById[query.info]) {
          $scope.g.modal.heatsink = privateScope.heatsinksById[query.info];
        } else {
          $scope.g.modal.heatsink = null;
        }
        if (privateScope.ppOptionsByValue[query.pp]) {
          $scope.g.pricePerformance = query.pp;
        } else {
          $scope.g.pricePerformance = null;
        }
      };
    })();

    var updatePath = (function () {
      function keys(obj) {
        var rv = [];
        for (var key in obj) {
          if (!obj.hasOwnProperty(key)) continue;
          rv.push(key);
        }
        return rv;
      }
      function serialize(obj) {
        var temp = [];
        for (var name in obj) {
          if (!obj.hasOwnProperty(name)) continue;
          temp.push(name + '=' + obj[name]);
        }
        return temp.join(QUERY_DELIMETER);
      }
      return function () {
        var query = {
          noise: $scope.g.noise,
          power: $scope.g.power,
          sort: $scope.g.sortOption.alias,
          maker: !$scope.g.filterByMaker ? '' :
              privateScope.makers.filter(function (maker) { return maker.selected; })
                                 .map(function (maker) { return maker.id; })
                                 .join(QUERY_ARRAY_DELIMETER),
          price: parseNumber($scope.g.priceMin, '') + '~' + parseNumber($scope.g.priceMax, ''),
          height: parseNumber($scope.g.heightMin, '') + '~' + parseNumber($scope.g.heightMax, ''),
          weight: parseNumber($scope.g.weightMin, '') + '~' + parseNumber($scope.g.weightMax, ''),
          type: $scope.g.heatsinkType,
          show: $scope.g.showSelectedOnly ? 'selection' : '',
          select: keys(privateScope.selectedHeatsinks).join(QUERY_ARRAY_DELIMETER),
          info: $scope.g.modal.heatsink ? $scope.g.modal.heatsink.id : '',
          pp: $scope.g.pricePerformance
        };
        if (query.noise === defaultValues.noise) delete query.noise;
        if (query.power === defaultValues.power) delete query.power;
        if (query.sort === defaultValues.sort) delete query.sort;
        if (query.maker === '') delete query.maker;
        if (query.price === '~') delete query.price;
        if (query.height === '~') delete query.height;
        if (query.weight === '~') delete query.weight;
        if (query.type === null) delete query.type;
        if (query.show === '') delete query.show;
        if (query.select === '') delete query.select;
        if (query.info === '') delete query.info;
        if (query.pp === null) delete query.pp;
        $location.path(serialize(query));
      };
    })();

    var defaultValues = {
      noise: 35,
      power: 62,
      sort: 'cpu'
    };

    var privateScope = {
      sortOptionsByAlias: indexBy($scope.sortOptions, 'alias'),
      heatsinkTypeOptionsByValue: indexBy($scope.heatsinkTypeOptions, 'value'),
      ppOptionsByValue: indexBy($scope.ppOptions, 'value'),
      selectedHeatsinks: {}
    };

    function ignoreInit(func) {
      return function (newValue, oldValue) {
        if (newValue === oldValue) return;
        func(newValue, oldValue);
      };
    }

    $q.all([
      getResources('/makers', 'makers'),
      getResources('/heatsinks', 'heatsinks'),
      getResources('/fan-configs', 'fanConfigs'),
      getResources('/measurements', 'measurements')
    ]).then(function () {
      $scope.makers = privateScope.makers;
      privateScope.makersByName = indexBy(privateScope.makers, 'name');
      readPath();
      attachProperties();
      selectMeasurements();
      $scope.$watch('g', updatePath, true);
      $scope.$watch('g.noise', ignoreInit(selectMeasurements));
      $scope.$watch('g.power', ignoreInit(selectMeasurements));
      $scope.$watch('g.sortOption', ignoreInit(sortMeasurements));
      $scope.$watch('g.priceMin', ignoreInit(updateMeasurementsVisibility));
      $scope.$watch('g.priceMax', ignoreInit(updateMeasurementsVisibility));
      $scope.$watch('g.heightMin', ignoreInit(updateMeasurementsVisibility));
      $scope.$watch('g.heightMax', ignoreInit(updateMeasurementsVisibility));
      $scope.$watch('g.weightMin', ignoreInit(updateMeasurementsVisibility));
      $scope.$watch('g.weightMax', ignoreInit(updateMeasurementsVisibility));
      $scope.$watch('g.heatsinkType', ignoreInit(updateMeasurementsVisibility));
      $scope.$watch('g.pricePerformance', ignoreInit(updateMeasurementsVisibility));
      $scope.$watch('g.showSelectedOnly', ignoreInit(updateMeasurementsVisibility));
      $scope.$watch('makers', function (makers) {
        updatePath();
        $scope.g.filterByMaker = makers.some(function (maker) { return maker.selected; });
        updateMeasurementsVisibility();
      }, true);
      $scope.$on('$locationChangeSuccess', readPath);

      // Wait for rendering to complete and set the snapshot status as ready
      $timeout(function () {
        $window.__snapshotStatus = 'ready';
      });
    });
  });

})();
