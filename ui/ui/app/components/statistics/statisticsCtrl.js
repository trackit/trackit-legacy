'use strict';

var module = angular.module('trackit.statistics')

module.controller('StatisticsCtrl', ['$scope', '$stateParams', '$http', 'Config',
	function($scope, $stateParams, $http, Config) {

		$scope.selectedChart = 0;

	}
]);
