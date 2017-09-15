"use strict";

var module = angular.module("trackit.aws.services", ["trackit.config"]);

module.factory("AWSKey", ["$resource", "Config",
  function ($resource, Config) {
  return $resource(Config.apiUrl("/aws/accounts/:id"), {}, {
    query: { method: "GET", params: {}},
    get: { method: "GET", params: {}},
    add: { method: "POST", params: {}},
    remove: { method: "DELETE", params: {}},
    change: {
      method: "PUT",
      params: {},
      url: Config.apiUrl("/aws/accounts/:id")
    }
  });
}]);
