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
    $scope.g = {};

    var sortOptionsByAlias = util.indexBy($scope.sortOptions, 'alias');

    var defaultValues = {
      noise: 35,
      power: 62,
      sort: 'cpu'
    };

    var getResources = function (url, name) {
      return $http.get(url).success(function (data) {
        $scope[name] = data.items;
        var map = {};
        for (var i = 0; i < data.items.length; i++) {
          var item = data.items[i];
          map[item.id] = item;
        }
        $scope[name + 'ById'] = map;
      }).error(function () {
        $scope.error = '데이터를 가져오는 동안 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.';
      });
    };

    var augmentMeasurements = function () {
      var empty = '-';
      for (var i = 0; i < $scope.measurements.length; i++) {
        var m = $scope.measurements[i];
        m.fan_config = $scope.fanConfigsById[m.fan_config_id];
        m.heatsink = $scope.heatsinksById[m.fan_config.heatsink_id];
        m.maker = $scope.makersById[m.heatsink.maker_id];
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
        m.price = m.heatsink.price ? (m.heatsink.price / 10000).toFixed(1) : '-';
        if (m.heatsink.danawa_id) {
          m.danawa_url = 'http://prod.danawa.com/info/?pcode=' + m.heatsink.danawa_id;
        }
        m.weight = m.heatsink.weight;
        m.height = m.heatsink.height;
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
        if ($scope.currentMeasurements.sortKey === key) return;
        $scope.currentMeasurements.items.sort(function (a, b) {
          var c;
          if ((c = compareNumbers(a, b, key)) != 0) return c;
          if ((c = compareNumbers(a, b, 'cpu_temp_delta')) != 0) return c;
          if ((c = compareNumbers(a, b, 'power_temp_delta')) != 0) return c;
          if ((c = compareNumbers(a, b, 'price')) != 0) return c;
          return 0;
        });
        $scope.currentMeasurements.sortKey = key;
      };
    })();

    var selectMeasurements = (function () {
      var cachedMeasurementSelections = {35: {}, 40: {}, 45: {}, 100: {}};
      return function () {
        var noise = $scope.g.noise,
            power = $scope.g.power;
        updateLocation();
        var cached = cachedMeasurementSelections[noise][power];
        if (cached) {
          $scope.currentMeasurements = cached;
          sortMeasurements();
          return;
        }
        var current = [];
        for (var i = 0; i < $scope.measurements.length; i++) {
          var m = $scope.measurements[i];
          if (m.noise === noise && m.power === power) {
            current.push(m);
          }
        }
        $scope.currentMeasurements = {
          sortKey: 'cpu_temp_delta',
          items: current
        };
        cachedMeasurementSelections[noise][power] = $scope.currentMeasurements;
        sortMeasurements();
      };
    })();

    var readLocation = function () {
      var query = util.deserialize($location.path().substr(1));
      $scope.g.noise = util.parseNumber(query.noise, defaultValues.noise);
      $scope.g.power = util.parseNumber(query.power, defaultValues.power);
      $scope.g.sortOption = sortOptionsByAlias[query.sort] ||
          sortOptionsByAlias[defaultValues.sort];
    };

    var updateLocation = function () {
      var query = {
        noise: $scope.g.noise,
        power: $scope.g.power,
        sort: $scope.g.sortOption.alias
      };
      if (query.noise === defaultValues.noise) delete query.noise;
      if (query.power === defaultValues.power) delete query.power;
      if (query.sort === defaultValues.sort) delete query.sort;
      $location.path(util.serialize(query));
    };

    readLocation();
    $q.all([
      getResources('/makers', 'makers'),
      getResources('/heatsinks', 'heatsinks'),
      getResources('/fan-configs', 'fanConfigs'),
      getResources('/measurements', 'measurements')
    ]).then(function () {
      augmentMeasurements();
      $scope.$watch('g', selectMeasurements, true);
      $scope.$watch('g.sortOption', sortMeasurements);
    });
  })

  .directive('barGraph', function () {
    return {
      scope: {'barGraph': '='},
      template: '<div class="bar">{@barGraph@}</div>',
      link: function (scope, element, attr) {
        scope.$watch('barGraph', function (value) {
          if (isNaN(value)) {
            element.addClass('invisible');
          } else {
            // Scale 25-90 to 0-100
            var width = Math.min(100, (value - 25) * (100 / 65)) + '%';
            element.find('.bar').css({width: width}).removeClass('invisible');
          }
        });
      }
    };
  })

  .service('util', function () {

    this.parseNumber = function (x, defaultValue) {
      x = Number(x);
      return isNaN(x) ? (defaultValue === undefined ? null : defaultValue) : x;
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

  .directive('boBindHtml', function ($sce) {
    return {
      link: function (scope, element, attr) {
        var unwatch = scope.$watch($sce.parseAsHtml(attr.boBindHtml), function (value) {
          element.html(value || '');
          unwatch();
        });
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
