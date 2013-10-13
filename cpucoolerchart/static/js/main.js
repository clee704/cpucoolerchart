(function () {
'use strict';

if (jQuery('html').hasClass('lt-ie8')) {
  jQuery('.get-new-browser img').each(function (index, element) {
    jQuery(element).attr('src', jQuery(element).data('src'));
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
