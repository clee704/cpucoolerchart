'use strict';

angular.module('cpucoolerchart', [])

  .config(function ($interpolateProvider) {
    $interpolateProvider.startSymbol('{@').endSymbol('@}');
  })

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
      heatsinkType: null
    };

    var privateScope = {
      sortOptionsByAlias: util.indexBy($scope.sortOptions, 'alias'),
      heatsinkTypeOptionsByValue: util.indexBy($scope.heatsinkTypeOptions, 'value')
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
        if (m.heatsink_size === [empty, empty, empty].join('x')) m.heatsink_size = empty;
        m.heatsink_weight = m.heatsink.weight === null ? empty :
            Math.round(m.heatsink.weight) + ' g';
        m.fan_size = m.fan_config.fan_size + '/' + m.fan_config.fan_thickness + 'T' +
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

    var findVisibleMeasurements = function () {
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
            (g.heatsinkType === null || g.heatsinkType === m.heatsink.heatsink_type);
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
        findVisibleMeasurements();
      };
    })();

    var readLocation = function () {
      var query = util.deserialize($location.path().substr(1));
      $scope.g.noise = util.parseNumber(query.noise, defaultValues.noise);
      $scope.g.power = util.parseNumber(query.power, defaultValues.power);
      $scope.g.sortOption = privateScope.sortOptionsByAlias[query.sort] ||
          privateScope.sortOptionsByAlias[defaultValues.sort];
      if (query.maker) {
        var makerNames = query.maker.split('/'),
            filtered = false;
        for (var i = 0; i < makerNames.length; i++) {
          var name = makerNames[i];
          var maker = privateScope.makersByName[name];
          if (maker) {
            maker.selected = true;
            filtered = true;
          }
        }
        $scope.g.filterByMaker = filtered;
      }
      if (query.price) {
        var values = query.price.split('~');
        $scope.g.priceMin = util.parseNumber(values[0]);
        $scope.g.priceMax = util.parseNumber(values[1]);
      }
      if (query.height) {
        var values = query.height.split('~');
        $scope.g.heightMin = util.parseNumber(values[0]);
        $scope.g.heightMax = util.parseNumber(values[1]);
      }
      if (query.weight) {
        var values = query.weight.split('~');
        $scope.g.weightMin = util.parseNumber(values[0]);
        $scope.g.weightMax = util.parseNumber(values[1]);
      }
      if (privateScope.heatsinkTypeOptionsByValue[query.type]) {
        $scope.g.heatsinkType = query.type;
      }
    };

    var updateLocation = function () {
      var query = {
        noise: $scope.g.noise,
        power: $scope.g.power,
        sort: $scope.g.sortOption.alias,
        maker: !$scope.g.filterByMaker ? '' :
            privateScope.makers.filter(function (maker) { return maker.selected; })
                               .map(function (maker) { return maker.name; })
                               .join('/'),
        price: util.parseNumber($scope.g.priceMin, '') + '~' + util.parseNumber($scope.g.priceMax, ''),
        height: util.parseNumber($scope.g.heightMin, '') + '~' + util.parseNumber($scope.g.heightMax, ''),
        weight: util.parseNumber($scope.g.weightMin, '') + '~' + util.parseNumber($scope.g.weightMax, ''),
        type: $scope.g.heatsinkType
      };
      if (query.noise === defaultValues.noise) delete query.noise;
      if (query.power === defaultValues.power) delete query.power;
      if (query.sort === defaultValues.sort) delete query.sort;
      if (query.maker === '') delete query.maker;
      if (query.price === '~') delete query.price;
      if (query.height === '~') delete query.height;
      if (query.weight === '~') delete query.weight;
      if (query.type === null) delete query.type;
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
      readLocation();
      augmentMeasurements();
      $scope.$watch('g', updateLocation, true);
      $scope.$watch('g.noise', selectMeasurements);
      $scope.$watch('g.power', selectMeasurements);
      $scope.$watch('g.sortOption', sortMeasurements);
      $scope.$watch('g.priceMin', findVisibleMeasurements);
      $scope.$watch('g.priceMax', findVisibleMeasurements);
      $scope.$watch('g.heightMin', findVisibleMeasurements);
      $scope.$watch('g.heightMax', findVisibleMeasurements);
      $scope.$watch('g.weightMin', findVisibleMeasurements);
      $scope.$watch('g.weightMax', findVisibleMeasurements);
      $scope.$watch('g.heatsinkType', findVisibleMeasurements);
      $scope.$watch('makers', function (makers) {
        updateLocation();
        $scope.g.filterByMaker = makers.some(function (maker) { return maker.selected; });
        findVisibleMeasurements();
      }, true);
      $scope.$on('$locationChangeSuccess', readLocation);
    });
  })

  .directive('barGraph', function (util) {
    return {
      template: '<div class="bar"></div>',
      link: function (scope, element, attr) {
        var value = scope.$eval(attr.barGraph),
            bar = element.find('.bar');
        bar.text(value);
        if (value === null || isNaN(value)) {
          element.addClass('invisible');
        } else {
          // Scale 25-90 to 0-100
          var width = Math.min(100, (value - 25) * (100 / 65)) + '%';
          bar.css({width: width}).removeClass('invisible');
        }
      }
    };
  })

  .service('util', function () {

    this.parseNumber = function (x, defaultValue) {
      if (x === null || x === undefined || x === '') {
        return (defaultValue === undefined ? null : defaultValue);
      }
      x = Number(x);
      return x === null || isNaN(x) ? (defaultValue === undefined ? null : defaultValue) : x;
    };

    this.serialize = function (obj) {
      var temp = [];
      for (var name in obj) {
        if (!obj.hasOwnProperty(name)) continue;
        temp.push(name + '=' + obj[name]);
      }
      return temp.join(',');
    };

    this.deserialize = function (str) {
      var obj = {},
          args = str.split(',');
      for (var i = 0; i < args.length; i++) {
        var x = args[i].split('='),
            name = x[0],
            value = x[1];
        obj[name] = value;
      }
      return obj;
    };

    this.indexBy = function (arr, value) {
      var map = {};
      for (var i = 0; i < arr.length; i++) {
        map[arr[i][value]] = arr[i];
      }
      return map;
    };
  })

  .directive('selectAll', function () {
    return {
      scope: {'items': '=selectAll'},
      link: function (scope, element, attr) {
        if (!element.is('input[type=checkbox]')) return;
        element.on('click', function () {
          scope.$apply(function () {
            var selected = element.is(':checked');
            for (var i = 0; i < scope.items.length; i++) {
              scope.items[i].selected = selected;
            }
          });
        });
      }
    };
  })

  .directive('center', function ($window, $timeout) {
    return {
      link: function (scope, element, attr) {
        element.css({
          position: 'fixed',
          zIndex: 100,
          width: attr.width + 'px',
          margin: 0
        });
        var win = angular.element($window);
        var resize = function () {
          element.css({
            top: ((win.height() - element.outerHeight()) / 2) + 'px',
            left: ((win.width() - element.outerWidth()) / 2) + 'px'
          });
        };
        win.on('resize', resize);
        $timeout(function () {
          resize();
        }, 100);
      }
    };
  })

  .directive('openLinksInNewWindow', function ($window) {
    return {
      link: function (scope, element/*, attr */) {
        element.on('click', 'a[href]', function (e) {
          if (e.ctrlKey || e.metaKey) return;
          var url = angular.element(e.target).attr('href');
          if (url && url.charAt(0) !== '#') {
            $window.open(url);
            e.preventDefault();
          }
        });
      }
    };
  })

  .directive('click', function () {
    return {
      link: function(scope, element, attr) {
        element.on('click', function (e) {
          scope.$apply(function () {
            scope.$eval(attr.click);
          });
          e.preventDefault();
        })
      }
    };
  })

  .directive('boBind', function () {
    return {
      link: function (scope, element, attr) {
        var unwatch = scope.$watch(attr.boBind, function (value) {
          element.text(value);
          unwatch();
        });
      }
    };
  })

  .directive('boAttr', function () {
    return {
      link: function (scope, element, attr) {
        var exprs = scope.$eval(attr.boAttr),
            unwatch = {};
        for (var name in exprs) {
          if (!exprs.hasOwnProperty(name)) continue;
          unwatch[name] = scope.$watch(exprs[name], (function (name) {
            return function (value) {
              if (name === 'class') {
                element.addClass(value);
              } else {
                element.attr(name, value);
              }
              unwatch[name]();
            };
          })(name));
        }
      }
    };
  })

  .directive('boIf', function () {
    return {
      link: function (scope, element, attr) {
        var unwatch = scope.$watch(attr.boIf, function (value) {
          if (!value) element.remove();
          unwatch();
        });
      }
    };
  });
