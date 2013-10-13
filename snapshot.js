var system = require('system');
var url = system.args[1] || '';
if (url.length > 0) {
  var page = require('webpage').create();
  page.open(url, function (status) {
    if (status === 'success') {
      var delay;
      var checker = function () {
        var html = page.evaluate(function () {
          if (window.__snapshotStatus === 'ready') {
            // Remove scripts
            [].forEach.call(document.querySelectorAll('script'), function (script) {
              script.parentNode.removeChild(script);
            });
            return document.querySelector('html').outerHTML;
          }
        });
        if (html) {
          clearTimeout(delay);
          console.log('<!DOCTYPE html>');
          console.log(html);
          phantom.exit();
        }
      };
      delay = setInterval(checker, 1000);
    }
  });
}