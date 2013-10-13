(function () {
'use strict';

if ($('html').hasClass('lt-ie8')) {
  $('.get-new-browser img').each(function (index, element) {
    $(element).attr('src', $(element).data('src'));
  });
  return;
}

angular.module('cpucoolerchart', [
    'cpucoolerchart.controllers',
    'cpucoolerchart.directives'
  ])
  .config(function ($interpolateProvider) {
    $interpolateProvider.startSymbol('{@').endSymbol('@}');
  })
  .value('QUERY_DELIMETER', '&')
  .value('QUERY_ARRAY_DELIMETER', ',');

})();
