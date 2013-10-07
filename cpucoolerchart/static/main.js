'use strict';

angular.module('cpucoolerchart', [])

  .config(function ($interpolateProvider) {
    $interpolateProvider.startSymbol('{@').endSymbol('@}');
  })

  .controller('DataCtrl', function ($scope, $http, $q) {
    $scope.g = {
      noise: 35,
      power: 62
    };

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

    var denormalizeMeasurements = function () {
      for (var i = 0; i < $scope.measurements.length; i++) {
        var m = $scope.measurements[i];
        m.fan_config = $scope.fanConfigsById[m.fan_config_id];
        m.heatsink = $scope.heatsinksById[m.fan_config.heatsink_id];
        m.maker = $scope.makersById[m.heatsink.maker_id];
        m.heatsink_size = [
          Math.round(m.heatsink.width) || '.',
          Math.round(m.heatsink.depth) || '.',
          Math.round(m.heatsink.height) || '.'
        ].join('x');
        if (m.heatsink_size === '.x.x.') m.heatsink_size = '.';
        m.heatsink_weight = m.heatsink.weight === null ? '.' :
            Math.round(m.heatsink.weight) + ' g';
        m.fan_size = m.fan_config.fan_size + '/' + m.fan_config.fan_thickness + 'T' +
            ' x' + m.fan_config.fan_count;
        m.rpm_avg = m.rpm_min === null ? '.' : Math.round((m.rpm_min + m.rpm_max) / 2) + ' rpm';
        if (m.power_temp_delta === null) {
          m.power_temp_delta = '.';
        }
        m.noise_avg = m.noise_actual_min === null ? '.' :
            (Math.round((m.noise_actual_min + m.noise_actual_max) / 2 * 10) / 10);
      }
    };

    $scope.cachedMeasurementSelections = {35: {}, 40: {}, 45: {}, 100: {}};
    var selectMeasurements = function () {
      var g = $scope.g;
      var cached = $scope.cachedMeasurementSelections[g.noise][g.power];
      if (cached) {
        $scope.currentMeasurements = cached;
        return;
      }
      var current = [];
      for (var i = 0; i < $scope.measurements.length; i++) {
        var m = $scope.measurements[i];
        if (m.noise === $scope.g.noise && m.power === $scope.g.power) {
          current.push(m);
        }
      }
      $scope.cachedMeasurementSelections[g.noise][g.power] = current;
      $scope.currentMeasurements = current;
    };

    $q.all([
      getResources('/makers', 'makers'),
      getResources('/heatsinks', 'heatsinks'),
      getResources('/fan-configs', 'fanConfigs'),
      getResources('/measurements', 'measurements')
    ]).then(function () {
      denormalizeMeasurements();
      $scope.$watch('g', function () {
        selectMeasurements();
      }, true);
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
            var width = Math.min(100, (value - 25) * (100 / 75)) + '%';
            element.find('.bar').css({width: width}).removeClass('invisible');
          }
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
        win.resize(resize);
        $timeout(function () {
          resize();
        }, 100);
      }
    };
  });
