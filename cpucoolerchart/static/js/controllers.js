'use strict';

angular.module('cpucoolerchart.controllers', ['cpucoolerchart.util'])

  .controller('DataCtrl', function ($scope, $http, $q, $location, util) {
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
    $scope.g = {
      priceMin: null,
      priceMax: null,
      heightMin: null,
      heightMax: null,
      weightMin: null,
      weightMax: null,
      heatsinkType: null,
      numSelectedHeatsinks: 0
    };

    var privateScope = {
      sortOptionsByAlias: util.indexBy($scope.sortOptions, 'alias'),
      heatsinkTypeOptionsByValue: util.indexBy($scope.heatsinkTypeOptions, 'value'),
      selectedHeatsinks: {}
    };

    var defaultValues = {
      noise: 35,
      power: 62,
      sort: 'cpu'
    };

    var getResources = function (url, name) {
      return $http.get(url).success(function (data) {
        privateScope[name] = data.items;
        privateScope[name + 'ById'] = util.indexBy(data.items, 'id');
      }).error(function () {
        $scope.error = '데이터를 가져오는 동안 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.';
      });
    };

    var augmentMeasurements = function () {
      var empty = '-';
      for (var i = 0; i < privateScope.measurements.length; i++) {
        var m = privateScope.measurements[i];
        m.fan_config = privateScope.fanConfigsById[m.fan_config_id];
        m.heatsink = privateScope.heatsinksById[m.fan_config.heatsink_id];
        m.maker = privateScope.makersById[m.heatsink.maker_id];
        m.heatsink_size = [
          Math.round(m.heatsink.width) || empty,
          Math.round(m.heatsink.depth) || empty,
          Math.round(m.heatsink.height) || empty
        ].join('x');
        if (m.heatsink_size === [empty, empty, empty].join('x')) {
          m.heatsink_size = empty;
        }
        m.heatsink_weight = m.heatsink.weight === null ? empty :
            Math.round(m.heatsink.weight) + ' g';
        m.fan_size = m.fan_config.fan_size + '/' +
            m.fan_config.fan_thickness + 'T' +
            ' x' + m.fan_config.fan_count;
        m.rpm_avg = m.rpm_min === null ? empty : Math.round((m.rpm_min + m.rpm_max) / 2) + ' rpm';
        if (m.power_temp_delta === null) {
          m.power_temp_delta = empty;
        }
        m.noise_avg = m.noise_actual_min === null ? empty :
            (Math.round((m.noise_actual_min + m.noise_actual_max) / 2 * 10) / 10);
        m.price_formatted = m.heatsink.price ? (m.heatsink.price / 10000).toFixed(1) : '-';
        if (m.heatsink.danawa_id) {
          m.danawa_url = 'http://prod.danawa.com/info/?pcode=' + m.heatsink.danawa_id;
        }
        m.price = m.heatsink.price === null ? null : m.heatsink.price / 10000;
        m.height = m.heatsink.height === null ? 0 : m.heatsink.height;
        m.weight = m.heatsink.weight === null ? 0 : m.heatsink.weight;
      }
    };

    var sortMeasurements = (function () {
      var compareNumbers = function (a, b, key) {
        var x = util.parseNumber(a[key]),
            y = util.parseNumber(b[key]);
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
          if ((c = compareNumbers(a, b, key)) != 0) return c;
          if ((c = compareNumbers(a, b, 'cpu_temp_delta')) != 0) return c;
          if ((c = compareNumbers(a, b, 'power_temp_delta')) != 0) return c;
          if ((c = compareNumbers(a, b, 'price')) != 0) return c;
          return 0;
        });
        $scope.measurements.sortKey = key;
      };
    })();

    var updateMeasurementsVisibility = function () {
      var g = $scope.g,
          filter = g.filterByMaker,
          current = $scope.measurements.items,
          found = false,
          length = 0;
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
            (!g.showSelectedOnly || m.heatsink.selected);
        m.first = !found && m.visible;
        if (m.first) found = true;
        if (m.visible) length += 1;
      }
      $scope.measurements.length = length;
    };

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
            if (m.noise === noise && m.power === power) {
              current.push(m);
            }
          }
          cachedMeasurementSelections[noise][power] = {
            sortKey: 'cpu_temp_delta',
            items: current
          };
          $scope.measurements = cachedMeasurementSelections[noise][power];
        }
        sortMeasurements();
        updateMeasurementsVisibility();
      };
    })();

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

    $scope.unselectAll = function () {
      var selected = privateScope.selectedHeatsinks;
      for (var id in selected) {
        if (!selected.hasOwnProperty(id)) continue;
        selected[id].selected = false;
        delete selected[id];
      }
      $scope.g.numSelectedHeatsinks = 0;
    };

    var readPath = function () {
      var query = util.deserialize($location.path().substr(1));
      $scope.g.noise = util.parseNumber(query.noise, defaultValues.noise);
      $scope.g.power = util.parseNumber(query.power, defaultValues.power);
      $scope.g.sortOption = privateScope.sortOptionsByAlias[query.sort] ||
          privateScope.sortOptionsByAlias[defaultValues.sort];
      $scope.g.filterByMaker = false;
      $scope.makers.forEach(function (maker) { maker.selected = false; });
      if (query.maker) {
        var makerIds = query.maker.split('|'),
            filtered = false;
        for (var i = 0; i < makerIds.length; i++) {
          var id = makerIds[i],
              maker = privateScope.makersById[id];
          if (!maker) continue;
          maker.selected = true;
          filtered = true;
        }
        $scope.g.filterByMaker = filtered;
      }
      if (query.price) {
        var values = query.price.split('~');
        $scope.g.priceMin = util.parseNumber(values[0]);
        $scope.g.priceMax = util.parseNumber(values[1]);
      } else {
        $scope.g.priceMin = $scope.g.priceMax = null;
      }
      if (query.height) {
        var values = query.height.split('~');
        $scope.g.heightMin = util.parseNumber(values[0]);
        $scope.g.heightMax = util.parseNumber(values[1]);
      } else {
        $scope.g.heightMin = $scope.g.heightMax = null;
      }
      if (query.weight) {
        var values = query.weight.split('~');
        $scope.g.weightMin = util.parseNumber(values[0]);
        $scope.g.weightMax = util.parseNumber(values[1]);
      } else {
        $scope.g.weightMin = $scope.g.weightMax = null;
      }
      if (privateScope.heatsinkTypeOptionsByValue.hasOwnProperty(query.type)) {
        $scope.g.heatsinkType = query.type;
      } else {
        $scope.g.heatsinkType = null;
      }
      if (query.show && query.show === 'selection') {
        $scope.g.showSelectedOnly = true;
      } else {
        $scope.g.showSelectedOnly = false;
      }
      $scope.unselectAll();
      if (query.select) {
        var heatsinkIds = query.select.split('|');
        for (var i = 0; i < heatsinkIds.length; i++) {
          var id = util.parseNumber(heatsinkIds[i]),
              heatsink = privateScope.heatsinksById[id];
          if (!heatsink) continue;
          $scope.toggleSelection(heatsink, true);
        }
      }
    };

    var updatePath = function () {
      var query = {
        noise: $scope.g.noise,
        power: $scope.g.power,
        sort: $scope.g.sortOption.alias,
        maker: !$scope.g.filterByMaker ? '' :
            privateScope.makers.filter(function (maker) { return maker.selected; })
                               .map(function (maker) { return maker.id; })
                               .join('|'),
        price: util.parseNumber($scope.g.priceMin, '') + '~' + util.parseNumber($scope.g.priceMax, ''),
        height: util.parseNumber($scope.g.heightMin, '') + '~' + util.parseNumber($scope.g.heightMax, ''),
        weight: util.parseNumber($scope.g.weightMin, '') + '~' + util.parseNumber($scope.g.weightMax, ''),
        type: $scope.g.heatsinkType,
        show: $scope.g.showSelectedOnly ? 'selection' : '',
        select: util.keys(privateScope.selectedHeatsinks).join('|')
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
      $location.path(util.serialize(query));
    };

    $q.all([
      getResources('/makers', 'makers'),
      getResources('/heatsinks', 'heatsinks'),
      getResources('/fan-configs', 'fanConfigs'),
      getResources('/measurements', 'measurements')
    ]).then(function () {
      $scope.makers = privateScope.makers;
      privateScope.makersByName = util.indexBy(privateScope.makers, 'name');
      readPath();
      augmentMeasurements();
      $scope.$watch('g', updatePath, true);
      $scope.$watch('g.noise', selectMeasurements);
      $scope.$watch('g.power', selectMeasurements);
      $scope.$watch('g.sortOption', sortMeasurements);
      $scope.$watch('g.priceMin', updateMeasurementsVisibility);
      $scope.$watch('g.priceMax', updateMeasurementsVisibility);
      $scope.$watch('g.heightMin', updateMeasurementsVisibility);
      $scope.$watch('g.heightMax', updateMeasurementsVisibility);
      $scope.$watch('g.weightMin', updateMeasurementsVisibility);
      $scope.$watch('g.weightMax', updateMeasurementsVisibility);
      $scope.$watch('g.heatsinkType', updateMeasurementsVisibility);
      $scope.$watch('g.showSelectedOnly', updateMeasurementsVisibility);
      $scope.$watch('makers', function (makers) {
        updatePath();
        $scope.g.filterByMaker = makers.some(function (maker) { return maker.selected; });
        updateMeasurementsVisibility();
      }, true);
      $scope.$on('$locationChangeSuccess', readPath);
    });
  });