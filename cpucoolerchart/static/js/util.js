'use strict';

angular.module('cpucoolerchart.util', [])

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

    this.keys = function (obj) {
      var keys = [];
      for (var key in obj) {
        if (!obj.hasOwnProperty(key)) continue;
        keys.push(key);
      }
      return keys;
    };
  });
