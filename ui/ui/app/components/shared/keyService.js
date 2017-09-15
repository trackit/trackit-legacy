"use strict";

var module = angular.module("trackit.key.services", ["ngRoute"]);

module.factory("Key", ["$location", "$routeParams", function ($location, $routeParams) {
  var url = $location.url();
  console.log("Url changed to", url);
  return url;
}]);
