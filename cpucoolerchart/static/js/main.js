'use strict';

angular.module('cpucoolerchart', [
    'cpucoolerchart.controllers',
    'cpucoolerchart.directives'
  ])
  .config(function ($interpolateProvider) {
    $interpolateProvider.startSymbol('{@').endSymbol('@}');
  })
  .value('QUERY_DELIMETER', '&')
  .value('QUERY_ARRAY_DELIMETER', ',');
