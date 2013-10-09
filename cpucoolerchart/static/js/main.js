'use strict';

angular.module('cpucoolerchart', [
    'cpucoolerchart.controllers',
    'cpucoolerchart.directives',
    'cpucoolerchart.util'
  ])
  .config(function ($interpolateProvider) {
    $interpolateProvider.startSymbol('{@').endSymbol('@}');
  });
