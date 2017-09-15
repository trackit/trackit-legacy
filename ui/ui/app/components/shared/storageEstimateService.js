'use strict';

var module = angular.module('trackit.storage', ['trackit.config']);

module.factory('StorageEstimate', function ($q, $http, Config) {
	var url = Config.apiUrl('/gcloud/estimate');

	return function (volumes) {
		var canceller = $q.defer();
		var promise = $http({
			method: 'GET',
			url: url,
			params: volumes,
			timeout: canceller,
		});

		function cancel() {
			canceller.resolve();
		}

		return {
			promise: promise,
			cancel: cancel,
		}
	}
});
