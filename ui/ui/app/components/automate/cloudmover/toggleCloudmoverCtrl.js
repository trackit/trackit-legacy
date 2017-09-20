'use strict';

var module = angular.module('trackit.cloudmover', [])

module.controller('ToggleCloudmoverCtrl', ['$scope', '$cookies', '$state',
    function($scope, $cookies, $state) {

        if ($cookies.get('cloudmover')) {
            $cookies.remove('cloudmover');
        } else {
            $cookies.put('cloudmover', 'true');
        }

        $state.go('app.home');

    }
]);
