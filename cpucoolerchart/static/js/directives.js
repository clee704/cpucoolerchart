'use strict';

angular.module('cpucoolerchart.directives', [])

  .directive('heatsinkInfo', function ($rootScope) {
    return {
      scope: {'g': '=scope'},
      link: function (scope, element, attr) {
        scope.$watch('g', function (value) {
          if (value.heatsink) {
            scope.heatsink = value.heatsink;
            element.modal('show');
          } else {
            element.modal('hide');
          }
        }, true);
        element.on('hidden.bs.modal', function () {
          scope.$apply(function () { scope.g.heatsink = null; });
        });
      }
    };
  })

  .directive('barGraph', function () {
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

  .directive('selectAll', function () {
    return {
      scope: {'items': '=selectAll'},
      link: function (scope, element) {
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
        function centerElement() {
          element.css({
            top: ((win.height() - element.outerHeight()) / 2) + 'px',
            left: ((win.width() - element.outerWidth()) / 2) + 'px'
          });
        }
        win.on('resize', centerElement);
        centerElement();
        scope.$watch(attr.center, function () {
          $timeout(function () {
            centerElement();
          });
        });
      }
    };
  })

  .directive('openLinkInNewWindow', function ($window) {
    return {
      link: function (scope, element/*, attr */) {
        element.on('click', function (e) {
          if (!(e.ctrlKey || e.metaKey || e.altKey || e.shiftKey)) {
            var url = angular.element(e.target).attr('href');
            if (url && url.charAt(0) !== '#') {
              $window.open(url);
              e.preventDefault();
            }
          }
          e.stopPropagation();
        });
      }
    };
  })

  .directive('click', function () {
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
          element.children().unwrap();
        } else {
          element.attr('href', url);
        }
      }
    };
  });
