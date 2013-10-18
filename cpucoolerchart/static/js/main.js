(function () {
'use strict';

if (jQuery('html').hasClass('lt-ie8')) {
  jQuery('.browser-choice img').each(function (index, element) {
    jQuery(element).attr('src', jQuery(element).data('src'));
  });
  return;
}

var browser = {
  ie: /MSIE/.test(navigator.userAgent) && !/Opera/.test(navigator.userAgent)
};

angular.module('cpucoolerchart', [])

  .config(function ($interpolateProvider) {
    $interpolateProvider.startSymbol('{@').endSymbol('@}');
  })

  .constant('DEFAULTS', {
    noise: 35,
    power: 62,
    sort: 'cpu'
  })
  .constant('OPTIONS', {
    noise: [
      {name: '35dB', value: 35},
      {name: '40dB', value: 40},
      {name: '45dB', value: 45},
      {name: '최대', value: 100}
    ],
    power: [
      {name: '62W', value: 62},
      {name: '92W', value: 92},
      {name: '150W', value: 150},
      {name: '200W', value: 200}
    ],
    sort: [
      {name: 'CPU 온도', value: 'cpu_temp_delta', alias: 'cpu'},
      {name: '전원부 온도', value: 'power_temp_delta', alias: 'power'},
      {name: '가격', value: 'price', alias: 'price'},
      {name: '높이', value: 'height', alias: 'height'},
      {name: '무게', value: 'weight', alias: 'weight'},
      {name: '소음', value: 'noise_avg', alias: 'noise'}
    ],
    heatsinkType: [
      {name: '타워', value: 'tower'},
      {name: '플라워', value: 'flower'}
    ],
    pp: [
      {name: '아주 좋음', value: 'best'},
      {name: '좋음', value: 'good'}
    ]
  })
  .constant('BAR_GRAPH_DOMAIN', [25, 90])
  .constant('QUERY_DELIMETER', '&')
  .constant('QUERY_ARRAY_DELIMETER', ',')
  .constant('QUERY_RANGE_DELIMETER', '~')
  .constant('PLOT_POINT_COLOR', '#006ba7')
  .constant('PLOT_POINT_OPACITY', 0.8)
  .constant('PLOT_POINT_RADIUS', 7)
  .constant('PLOT_POINT_RADIUS_HOVER', 9)
  .constant('PLOT_POINT_SELECTED_STROKE_WIDTH', 4)
  .constant('PLOT_LABEL_MARGIN', 3)
  .constant('PLOT_TOOLTIP_PADDING', {top: 7, right: 9, bottom: 7, left: 9})
  .constant('PLOT_TOOLTIP_MARGIN', 10)
  .constant('PLOT_TRANSITION_DURATION', 400)

  .controller('DataCtrl', function ($scope, $http, $q, $window, $timeout,
                                    DEFAULTS, OPTIONS, PathSync, util) {

    $scope.options = OPTIONS;
    $scope.g = {modal: {}};
    $scope.loading = {};

    $scope.clearSelection = function () {
      for (var i = 0; i < $scope.heatsinks.length; i++) {
        $scope.heatsinks[i].selected = false;
      }
    };

    var privateScope = {};

    $q.all([
      getResources('/makers', 'makers'),
      getResources('/heatsinks', 'heatsinks'),
      getResources('/fan-configs', 'fanConfigs'),
      getResources('/measurements', 'measurements')
    ]).then(function () {
      $scope.makers = privateScope.makers;
      $scope.heatsinks = privateScope.heatsinks;
      attachProperties();

      var pathSync = new PathSync($scope);
      pathSync.config([{
        name: 'noise',
        type: 'number',
        expr: 'g.noise',
        options: $scope.options.noise,
        defaultValue: DEFAULTS.noise,
        callback: selectMeasurements
      }, {
        name: 'power',
        type: 'number',
        expr: 'g.power',
        options: $scope.options.power,
        defaultValue: DEFAULTS.power,
        callback: selectMeasurements
      }, {
        name: 'sort',
        type: 'option',
        expr: 'g.sortOption',
        options: $scope.options.sort,
        key: 'alias',
        defaultValue: DEFAULTS.sort,
        callback: sortMeasurements
      }, {
        name: 'maker',
        type: 'list',
        expr: 'makers',
        key: 'id',
        marker: 'selected',
        sizeExpr: 'g.numSelectedMakers',
        callback: function () {
          $scope.g.filterByMaker = $scope.g.numSelectedMakers > 0;
          updateMeasurementsVisibility();
        }
      }, {
        name: 'price',
        type: 'range',
        exprs: ['g.priceMin', 'g.priceMax'],
        callback: updateMeasurementsVisibility
      }, {
        name: 'height',
        type: 'range',
        exprs: ['g.heightMin', 'g.heightMax'],
        callback: updateMeasurementsVisibility
      }, {
        name: 'weight',
        type: 'range',
        exprs: ['g.weightMin', 'g.weightMax'],
        callback: updateMeasurementsVisibility
      }, {
        name: 'type',
        type: 'value',
        expr: 'g.heatsinkType',
        options: $scope.options.heatsinkType,
        defaultValue: null,
        callback: updateMeasurementsVisibility
      }, {
        name: 'select',
        type: 'list',
        expr: 'heatsinks',
        key: 'id',
        marker: 'selected',
        sizeExpr: 'g.numSelectedHeatsinks',
        callback: updateMeasurementsVisibility
      }, {
        name: 'pp',
        type: 'value',
        expr: 'g.pricePerformance',
        options: $scope.options.pp,
        defaultValue: null,
        callback: updateMeasurementsVisibility
      }, {
        name: 'show',
        type: 'bool',
        expr: 'g.showSelectedOnly',
        trueValue: 'selection',
        falseValue: null,
        defaultValue: null,
        callback: updateMeasurementsVisibility
      }, {
        name: 'pane',
        type: 'value',
        expr: 'g.pane',
        options: [{value: 'table'}, {value: 'plot'}],
        defaultValue: 'table'
      }, {
        name: 'info',
        type: 'option',
        expr: 'g.modal.heatsink',
        options: privateScope.heatsinks,
        key: 'id',
        defaultValue: null
      }, {
        name: 'fixdomain',
        type: 'bool',
        expr: 'g.fixDomain',
        trueValue: 't',
        falseValue: null,
        defaultValue: null
      }, {
        name: 'shownames',
        type: 'bool',
        expr: 'g.showNames',
        trueValue: 't',
        falseValue: null,
        defaultValue: null
      }]);
      pathSync.start();

      selectMeasurements();

      // Wait for rendering to complete and set the snapshot status as ready
      $timeout(function () {
        $window.__snapshotStatus = 'ready';
      });
    });

    function getResources(url, name) {
      $scope.loading[name] = true;
      return $http.get(url).success(function (data) {
        privateScope[name] = data.items;
        privateScope[name + 'ById'] = util.indexBy(data.items, 'id');
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
          if ((c = compareNumbers(a, b, key)) !== 0) return c;
          if ((c = compareNumbers(a, b, 'cpu_temp_delta')) !== 0) return c;
          if ((c = compareNumbers(a, b, 'power_temp_delta')) !== 0) return c;
          if ((c = compareNumbers(a, b, 'price')) !== 0) return c;
          return 0;
        });
        $scope.measurements.sortKey = key;
        findFirstVisibleMeasurement();
      };
    })();

    function updateMeasurementsVisibility() {
      var g = $scope.g,
          length = 0;
      if (g.pricePerformance) calculatePricePerformance();
      for (var i = 0; i < $scope.measurements.items.length; i++) {
        var m = $scope.measurements.items[i];
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
        if (m.visible) length += 1;
      }
      $scope.measurements.length = length;
      findFirstVisibleMeasurement();
    }

    function findFirstVisibleMeasurement() {
      var found = false;
      for (var i = 0; i < $scope.measurements.items.length; i++) {
        var m = $scope.measurements.items[i];
        m.first = false;
        if (!found && m.visible) {
          m.first = true;
          found = true;
        }
      }
    }

    function calculatePricePerformance() {
      var g = $scope.g,
          current = $scope.measurements.items,
          thresholds = {
            best: {price: 0.25, temp: 0.5, tempRatio: 10, priceRatio: 6},
            good: {price: 0.5, temp: 1, tempRatio: 15, priceRatio: 9}
          },
          lastPrice, lastCpuTemp, i, m, best, refPoint, x, y, ratio,
          priceLimit, tempLimit, best1, best2;
      // Pass 1: ascend CPU temp from low to high
      var orderedByCpuTemp = current.slice(0);
      orderedByCpuTemp.sort(function (a, b) { return a.cpu_temp_delta - b.cpu_temp_delta; });
      lastPrice = null;
      lastCpuTemp = null;
      for (i = 0; i < orderedByCpuTemp.length; i++) {
        m = orderedByCpuTemp[i];
        if (!m.price) continue;
        best = false;
        refPoint = false;
        if (lastPrice === null) {
          best = true;
          refPoint = true;
        } else {
          x = lastPrice - m.price;
          y = m.cpu_temp_delta - lastCpuTemp;
          ratio = thresholds[g.pricePerformance].tempRatio;
          priceLimit = thresholds[g.pricePerformance].price;
          tempLimit = thresholds[g.pricePerformance].temp;
          best1 = y / x < ratio && x >= 0;
          best2 = (x * x) / (priceLimit * priceLimit) + (y * y) / (tempLimit * tempLimit) < 1;
          best = best1 || best2;
          refPoint = best1;
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
        best = false;
        refPoint = false;
        if (lastCpuTemp === null) {
          best = true;
          refPoint = true;
        } else {
          x = lastCpuTemp - m.cpu_temp_delta;
          y = m.price - lastPrice;
          ratio = thresholds[g.pricePerformance].priceRatio;
          priceLimit = thresholds[g.pricePerformance].price;
          tempLimit = thresholds[g.pricePerformance].temp;
          best1 = y / x < ratio && x >= 0;
          best2 = (x * x) / (tempLimit * tempLimit) + (y * y) / (priceLimit * priceLimit) < 1;
          best = best1 || best2;
          refPoint = best1;
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
  })

  .factory('PathSync', function ($location, $parse,
      QUERY_DELIMETER, QUERY_ARRAY_DELIMETER, QUERY_RANGE_DELIMETER, util) {

    function PathSync(scope) {
      this._scope = scope;
      this._variables = [];
      this._variablesByName = {};
      this._started = false;
      this._query = {};
    }

    PathSync.prototype.config = function (config) {
      for (var i = 0; i < config.length; i++) {
        this._variable(config[i]);
      }
    };

    // TODO: Use inheritance instead of v.type
    // Methods to be affected: _variable, start, _readPath, _updateQuery

    PathSync.prototype._variable = function (v) {
      if (v.type === 'number' || v.type === 'value') {
        v.allowedValues = util.indexBy(v.options, 'value');
      } else if (v.type === 'option') {
        v.allowedValues = util.indexBy(v.options, v.key);
      } else if (v.type === 'range') {
        v.defaultValue = QUERY_RANGE_DELIMETER;
      } else if (v.type === 'list') {
        v.defaultValue = '';
        v.watchExpr = function (scope) {
          var items = scope.$eval(v.expr),
              rv = {};
          for (var i = 0; i < items.length; i++) {
            var item = items[i];
            rv[item[v.key]] = item[v.marker];
          }
          return rv;
        };
      }
      var updateFunc = this._ignoreInit(this._updatePath.bind(this, v.name)),
          userCallback = this._ignoreInit(v.callback);
      v.watchCallback = function (newValue, oldValue, scope) {
        if (v.type === 'list') $parse(v.sizeExpr).assign(scope, util.sum(util.values(newValue)));
        updateFunc(newValue, oldValue, scope);
        if (v.callback) userCallback(newValue, oldValue, scope);
      };
      this._variables.push(v);
      this._variablesByName[v.name] = v;
    };

    PathSync.prototype.start = function () {
      if (this._started) return;
      this._started = true;
      this._readPath();
      this._scope.$on('$locationChangeSuccess', this._readPath.bind(this));
      for (var i = 0; i < this._variables.length; i++) {
        var v = this._variables[i];
        if (v.type === 'range') {
          this._scope.$watch(v.exprs[0], v.watchCallback);
          this._scope.$watch(v.exprs[1], v.watchCallback);
        } else if (v.type === 'list') {
          this._scope.$watchCollection(v.watchExpr, v.watchCallback);
        } else {
          this._scope.$watch(v.expr, v.watchCallback);
        }
      }
    };

    PathSync.prototype._readPath = function () {
      this._query = this._deserialize($location.path().substr(1));
      for (var i = 0; i < this._variables.length; i++) {
        var v = this._variables[i],
            rawValue = this._query[v.name],
            val, values;
        if (v.type === 'range') {
          values = rawValue && rawValue.split(QUERY_RANGE_DELIMETER) || [];
          $parse(v.exprs[0]).assign(this._scope, util.parseNumber(values[0]));
          $parse(v.exprs[1]).assign(this._scope, util.parseNumber(values[1]));
        } else if (v.type === 'list') {
          var keys = util.indexBy(rawValue ? rawValue.split(QUERY_ARRAY_DELIMETER) : []),
              items = this._scope.$eval(v.expr);
          for (var j = 0; j < items.length; j++) {
            var item = items[j];
            item[v.marker] = !!keys[item[v.key]];
          }
        } else {
          val = v.type === 'number' ? util.parseNumber(rawValue, v.defaultValue) :
              v.type === 'bool' ? rawValue === v.trueValue :
              rawValue;
          if (v.type !== 'bool' && v.allowedValues[val] === undefined) val = v.defaultValue;
          if (v.type === 'option') val = v.allowedValues[val];
          $parse(v.expr).assign(this._scope, val);
        }
        this._updateQuery(v.name);
      }
      for (var name in this._query) {
        if (!this._query.hasOwnProperty(name)) continue;
        if (!this._variablesByName[name]) delete this._query[name];
      }
      $location.path(this._serialize(this._query));
    };

    PathSync.prototype._updateQuery = function (name) {
      var v = this._variablesByName[name],
          val, values, queryValue;
      if (!v) return;
      if (v.type === 'range') {
        values = [
          util.parseNumber(this._scope.$eval(v.exprs[0]), ''),
          util.parseNumber(this._scope.$eval(v.exprs[1]), '')
        ];
        queryValue = values.join(QUERY_RANGE_DELIMETER);
      } else if (v.type === 'list') {
        var items = this._scope.$eval(v.expr),
            keys = [];
        for (var j = 0; j < items.length; j++) {
          var item = items[j];
          if (item[v.marker]) keys.push(item[v.key]);
        }
        queryValue = keys.join(QUERY_ARRAY_DELIMETER);
      } else {
        val = this._scope.$eval(v.expr);
        queryValue = v.type === 'option' ? val && val[v.key] || null :
            v.type === 'bool' ? (val ? v.trueValue : v.falseValue) :
            val;
      }
      if (queryValue !== v.defaultValue) {
        this._query[name] = queryValue;
      } else {
        delete this._query[name];
      }
    };

    PathSync.prototype._updatePath = function (name) {
      this._updateQuery(name);
      $location.path(this._serialize(this._query));
    };

    PathSync.prototype._ignoreInit = function (func) {
      return function (newValue, oldValue, scope) {
        if (newValue === oldValue) return;
        func.call(this, newValue, oldValue, scope);
      };
    };

    PathSync.prototype._serialize = function (obj) {
      var temp = [];
      for (var name in obj) {
        if (!obj.hasOwnProperty(name)) continue;
        temp.push(name + '=' + obj[name]);
      }
      return temp.join(QUERY_DELIMETER);
    };

    PathSync.prototype._deserialize = function (str) {
      var obj = {},
          args = str.split(QUERY_DELIMETER);
      for (var i = 0; i < args.length; i++) {
        var x = args[i].split('='),
            name = x[0],
            value = x[1];
        if (value === undefined) continue;
        obj[name] = value;
      }
      return obj;
    };

    return PathSync;
  })

  .directive('barGraph', function (BAR_GRAPH_DOMAIN) {
    var scale = d3.scale.linear().domain(BAR_GRAPH_DOMAIN).range([0, 100]).clamp(true);
    return {
      template: '<div class="bar"></div>',
      link: function (scope, element, attr) {
        var value = scope.$eval(attr.barGraph),
            bar = element.find('.bar');
        bar.text(value);
        if (value === null || isNaN(value)) {
          element.addClass('invisible');
        } else {
          var width = scale(value) + '%';
          bar.css({width: width}).removeClass('invisible');
        }
      }
    };
  })

  .directive('scatterPlot', function ($window, $timeout, throttle,
      PLOT_POINT_COLOR, PLOT_POINT_OPACITY, PLOT_POINT_RADIUS,
      PLOT_POINT_RADIUS_HOVER, PLOT_POINT_SELECTED_STROKE_WIDTH,
      PLOT_LABEL_MARGIN, PLOT_TOOLTIP_PADDING, PLOT_TOOLTIP_MARGIN,
      PLOT_TRANSITION_DURATION) {
    return {
      link: function (scope, element, attr) {

        if (!angular.element('html').hasClass('svg')) return;

        function translate(selection, x, y) {
          selection.attr('transform', 'translate(' + x + ',' + y + ')');
        }

        var margin = {top: 10, right: 10, bottom: 20, left: 40},
            svgWidthMin = 0,
            svgWidth, svgHeight, plotWidth, plotHeight;

        // Scales
        var x = d3.scale.linear();
        var y = d3.scale.linear();

        // Axes
        var xAxis = function () { return d3.svg.axis().scale(x).orient('bottom'); };
        var yAxis = function () { return d3.svg.axis().scale(y).orient('left'); };

        // Root element and wrapper element (margin applied)
        var svg = d3.select(element[0]).append('svg');
        var wrapper = svg.append('g').call(translate, margin.left, margin.top);

        // Axes elements
        var xAxisWrapper = wrapper.append('g')
            .attr('class', 'x axis');
        xAxisWrapper.append('text')
            .attr('dy', '-.71em')
            .style('text-anchor', 'end')
            .text('가격 (만원)');
        var yAxisWrapper = wrapper.append('g')
            .attr('class', 'y axis');
        yAxisWrapper.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('y', 6)
            .attr('dy', '.71em')
            .style('text-anchor', 'end')
            .text('CPU 온도 (°C)');

        // Accessors
        var xValue = function (d) { return d.price; };
        var yValue = function (d) { return d.cpu_temp_delta; };
        var xValueScaled = function (d) { return x(xValue(d)); };
        var yValueScaled = function (d) { return y(yValue(d)); };

        var id = function (d) {
          return d.fan_config.id;
        };
        var visible = function (d) {
          return d.price && d.visible;
        };
        var priority = function (d) {
          return d.heatsink.selected ? 1 : 0;
        };
        var orderByPriority = function (a, b) {
          return priority(a) - priority(b);
        };

        var labelsWrapper = wrapper.append('g')
            .attr('class', 'labels');

        var pointsWrapper = wrapper.append('g');

        // Tooltip (show on hover)
        var tooltipWrapper = wrapper.append('g')
            .attr('class', 'point-tooltip')
            .style('opacity', 0);
        tooltipWrapper.append('rect');
        var tooltip = tooltipWrapper.append('text')
            .call(translate, PLOT_TOOLTIP_PADDING.left, PLOT_TOOLTIP_PADDING.top);
        var tooltipLines = [
          tooltip.append('tspan'),
          tooltip.append('tspan'),
          tooltip.append('tspan')
        ];
        tooltip.selectAll('tspan')
            .attr('x', 0)
            .attr('dy', function (d, i) { return i === 0 ? '1em' : '1.6em'; });

        function hideTooltip() {
          tooltipWrapper.style('opacity', 0);
          tooltipWrapper.select('rect').attr({'width': '0', 'height': 0});
          tooltip.selectAll('tspan').text('');
        }

        var lastData = null;

        // Interactions for points
        var onclick = function (d) {
          scope.$apply(function () {
            d.heatsink.selected = !d.heatsink.selected;
          });
        };

        var onmouseover = function (d) {
          if (!visible(d)) return;

          // Move the point to the front
          if (this.nextSibling) this.parentNode.appendChild(this);

          // Enlarge the point and make it opaque
          d3.select(this)
              .attr('r', PLOT_POINT_RADIUS_HOVER - PLOT_POINT_SELECTED_STROKE_WIDTH / 2)
              .style('opacity', 1);

          // Set tooltip text
          tooltipLines[0].text(d.maker.name + ' ' + d.heatsink.name);
          tooltipLines[1].text('가격: ' + xValue(d));
          tooltipLines[2].text('CPU 온도: ' + yValue(d));

          // Compute the position and size of the tooltip
          var r = PLOT_POINT_RADIUS_HOVER,
              spacing = PLOT_TOOLTIP_MARGIN,
              x = Math.floor(xValueScaled(d) + r + spacing),
              y = Math.floor(yValueScaled(d) - r),
              bbox = tooltip.node().getBBox(),
              width = bbox.width + PLOT_TOOLTIP_PADDING.left + PLOT_TOOLTIP_PADDING.right,
              height = bbox.height + PLOT_TOOLTIP_PADDING.top + PLOT_TOOLTIP_PADDING.bottom;
          if (x + width >= plotWidth + margin.right) x -= width + (r + spacing) * 2;
          if (y + height >= plotHeight + margin.bottom) y -= height - r * 2;
          tooltipWrapper
              .call(translate, x, y)
              .style('opacity', 1);
          tooltipWrapper.select('rect')
              .attr('width', width + 'px')
              .attr('height', height + 'px');
        };

        var onmouseout = function (d) {
          if (!visible(d)) return;
          hideTooltip();
          // Apply normal styles
          d3.select(this)
              .attr('r', PLOT_POINT_RADIUS - PLOT_POINT_SELECTED_STROKE_WIDTH / 2)
              .style('opacity', PLOT_POINT_OPACITY);
          // Move the point to where it originally was
          pointsWrapper.selectAll('circle')
              .data(lastData, id)
              .order();
        };

        var domainSet = false;

        function setDomains(fixed) {
          domainSet = true;
          if (fixed) {
            x.domain([0, 24]);
            y.domain([40, 100]);
          } else {
            var filtered = lastData.filter(visible);
            x.domain(d3.extent(filtered, xValue)).nice();
            y.domain(d3.extent(filtered, yValue)).nice();
          }
        }

        function updateDimensions(duration) {
          var elementWidth = element.width();
          var viewportHeight = angular.element($window).height();
          if (svgWidthMin > elementWidth) {
            element.css('overflow-x', 'auto');
          } else {
            element.css('overflow-x', '');
          }
          svgWidth = Math.max(svgWidthMin, elementWidth);
          svgHeight = Math.min(Math.floor(svgWidth / 1.1), viewportHeight - 200);
          plotWidth = svgWidth - margin.left - margin.right;
          plotHeight = svgHeight - margin.top - margin.bottom;

          x.range([0, plotWidth]);
          y.range([plotHeight, 0]);
          svg.attr('width', svgWidth).attr('height', svgHeight);
          xAxisWrapper.call(translate, 0, plotHeight);
          xAxisWrapper.select('text').transition().duration(duration)
              .attr('x', plotWidth);
        }

        function updateElements(duration) {
          xAxisWrapper.transition().duration(duration).call(xAxis());
          yAxisWrapper.transition().duration(duration).call(yAxis());
          pointsWrapper.selectAll('circle').transition().duration(duration)
              .attr({
                'cx': xValueScaled,
                'cy': yValueScaled,
                'r': PLOT_POINT_RADIUS - PLOT_POINT_SELECTED_STROKE_WIDTH / 2
              })
              .style({
                'fill': function (d) {
                  return d.heatsink.selected ? '#fff' : PLOT_POINT_COLOR;
                },
                'opacity': function (d) {
                  return visible(d) ? PLOT_POINT_OPACITY : 0;
                }
              });
          var showNames = scope.$eval(attr.showNames);
          var offset = PLOT_POINT_RADIUS + PLOT_LABEL_MARGIN;
          labelsWrapper.selectAll('text').transition().duration(duration)
              .attr({'x': xValueScaled, 'y': yValueScaled})
              .style('opacity', function (d) {
                return showNames && visible(d) ? 1 : 0;
              })
          .each('end', function () {
            var selection = d3.select(this);
            var dx = selection.attr('dx');
            selection.transition().duration(duration)
                .attr('dx', function (d) {
                  var bbox = this.getBBox(),
                      right = bbox.x + bbox.width + (offset - dx);
                  if (right >= plotWidth + margin.right) {
                    return -(offset + bbox.width);
                  } else {
                    return offset;
                  }
                });
          });
        }

        scope.$watch(function (scope) {
          var rv = {};
          var data = scope.$eval(attr.data);
          if (data) {
            for (var i = 0; i < data.length; i++) {
              var d = data[i];
              rv[d.id] = {visible: d.visible, selected: d.heatsink.selected};
            }
          }
          return rv;
        }, function () {
          var data = scope.$eval(attr.data);
          if (data === undefined) return;
          lastData = data.slice(0).sort(orderByPriority);

          setDomains(scope.$eval(attr.fixDomain));

          var points = pointsWrapper.selectAll('circle')
              .data(lastData, id)
              .order();
          points.enter().append('circle')
              .style('fill', PLOT_POINT_COLOR)
              .style('stroke', PLOT_POINT_COLOR)
              .style('stroke-width', PLOT_POINT_SELECTED_STROKE_WIDTH + 'px')
              .style('opacity', 0)
              .on('click', onclick)
              .on('mouseover', onmouseover)
              .on('mouseout', onmouseout);

          var labels = labelsWrapper.selectAll('text')
              .data(lastData, id)
              .order();
          labels.enter().append('text')
              .attr('dx', PLOT_POINT_RADIUS + PLOT_LABEL_MARGIN)
              .style('opacity', 0)
              .text(function (d) { return d.heatsink.name; });

          updateDimensions(0);
          updateElements(PLOT_TRANSITION_DURATION);
          points.exit().transition().duration(PLOT_TRANSITION_DURATION)
              .style('opacity', 0).remove();
          labels.exit().transition().duration(PLOT_TRANSITION_DURATION)
              .style('opacity', 0).remove();
          hideTooltip();
        }, true);

        scope.$watch(attr.resize, function (shouldResize) {
          if (!shouldResize) return;
          $timeout(function () {
            updateDimensions(0);
            updateElements(0);
          });
        });

        scope.$watch(attr.fixDomain, function (fixDomain) {
          if (lastData) {
            setDomains(fixDomain);
            updateElements(PLOT_TRANSITION_DURATION);
          }
        });

        scope.$watch(attr.showNames, function (showNames) {
          labelsWrapper.selectAll('text').transition().duration(PLOT_TRANSITION_DURATION)
              .style('opacity', function (d) {
                return showNames && visible(d) ? 1 : 0;
              })
        });

        angular.element($window).on('resize', throttle(function () {
          updateDimensions(0);
          updateElements(0);
        }, 200));
      }
    };
  })

  .directive('heatsinkInfoModal', function () {
    return {
      scope: {'parent': '='},
      link: function (scope, element) {
        // Show the dialog depending on whether the heatsink variable is assigned
        scope.$watch('parent.heatsink', function (heatsink) {
          if (heatsink) {
            scope.heatsink = heatsink;
            element.modal('show');
          } else {
            element.modal('hide');
          }
        });
        // The modal dialog can be closed outside this app by bootstrap.js,
        // i.e. when the backdrop is clicked. The heatsink variable should be
        // cleared when the modal is closed.
        element.on('hidden.bs.modal', function () {
          scope.$apply(function () { scope.parent.heatsink = null; });
        });
      }
    };
  })

  // Assign true or false to the `selected` property of the given items.
  .directive('selectAll', function () {
    return {
      scope: {'items': '=selectAll'},
      link: function (scope, element) {
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

  .directive('button', function () {
    return {
      restrict: 'E',
      link: function (scope, element) {
        // Fix an issue in Chrome and IE:
        // Buttons remain focused when clicked by mouse. They should not
        // and only should when clicked by keyboard.
        element.on('mouseup', function () { element.blur(); });
      }
    };
  })

  // Center the element relative to the viewport.
  .directive('center', function ($window, $timeout) {
    return {
      link: function (scope, element, attr) {
        element.css({
          position: 'fixed',
          zIndex: 10000,
          width: attr.width + 'px',
          margin: 0
        });
        var wnd = angular.element($window);
        function centerElement() {
          element.css({
            top: ((wnd.height() - element.outerHeight()) / 2) + 'px',
            left: ((wnd.width() - element.outerWidth()) / 2) + 'px'
          });
        }
        wnd.on('resize', centerElement);
        centerElement();
        scope.$watch(attr.center, function () {
          $timeout(centerElement);
        });
      }
    };
  })

  // An alternative to ngClick. Only fired when meta keys are not pressed.
  // Supports preventDefault and stopPropagation.
  .directive('click', function ($window) {
    return {
      link: function(scope, element, attr) {
        element.on('click', function (e) {
          if (!(e.ctrlKey || e.metaKey || e.altKey || e.shiftKey)) {
            scope.$apply(function () {
              scope.$eval(attr.click);
            });
            if (attr.hasOwnProperty('preventDefault')) e.preventDefault();
          }
          if (attr.hasOwnProperty('stopPropagation')) e.stopPropagation();
        });
      }
    };
  })

  .directive('boBind', function () {
    return {
      link: function (scope, element, attr) {
        element.text(scope.$eval(attr.boBind));
      }
    };
  })

  .directive('boBindUnwrap', function () {
    return {
      link: function (scope, element, attr) {
        element.text(scope.$eval(attr.boBindUnwrap)).contents().unwrap();
      }
    };
  })

  .directive('boAttr', function () {
    return {
      link: function (scope, element, attr) {
        var exprs = scope.$eval(attr.boAttr);
        for (var name in exprs) {
          if (!exprs.hasOwnProperty(name)) continue;
          var value = exprs[name];
          if (name === 'class') {
            element.addClass(value);
          } else {
            element.attr(name, value);
          }
        }
      }
    };
  })

  .directive('boIf', function () {
    return {
      link: function (scope, element, attr) {
        if (!scope.$eval(attr.boIf)) element.remove();
      }
    };
  })

  .directive('linkIf', function () {
    return {
      link: function (scope, element, attr) {
        var url = scope.$eval(attr.linkIf);
        if (!url) {
          element.contents().unwrap();
        } else {
          element.attr('href', url);
        }
      }
    };
  })

  .service('util', function () {
    this.indexBy = function (arr, value) {
      var map = {};
      for (var i = 0; i < arr.length; i++) {
        var item = arr[i];
        map[value === undefined ? item : item[value]] = item;
      }
      return map;
    };
    this.values = function (obj) {
      var rv = [];
      for (var name in obj) {
        if (!obj.hasOwnProperty(name)) continue;
        rv.push(obj[name]);
      }
      return rv;
    };
    this.sum = function (arr) {
      var rv = 0;
      for (var i = 0; i < arr.length; i++) rv += arr[i];
      return rv;
    };
    this.parseNumber = function (x, defaultValue) {
      if (defaultValue === undefined) defaultValue = null;
      if (x === null || x === undefined || x === '') return defaultValue;
      x = Number(x);
      return x === null || isNaN(x) ? defaultValue : x;
    };
  })

  // Returns a new function which guarantees that the wrapped function is run
  // no frequently than the given rate (in milliseconds).
  .factory('throttle', function ($timeout) {
    return function (fn, rate) {
      var timerId,
          lastFired;
      function run() {
        var args = arguments,
            now = Date.now();
        if (lastFired === undefined || lastFired + rate > now) {
          if (timerId !== undefined) $timeout.cancel(timerId);
          timerId = $timeout(function () { run.apply(null, args); }, rate);
        } else {
          fn.apply(null, args);
        }
        lastFired = now;
      }
      return run;
    };
  });

})();
