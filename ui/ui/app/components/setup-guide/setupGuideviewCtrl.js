'use strict';

module.controller('setupGuideviewCtrl', ['$scope', '$http', 'Config', 'AWSKey', '$cookies', '$rootScope',
    function($scope, $http, Config, AWSKey, $cookies, $rootScope) {
        if ($rootScope.userToken) {
            $scope.backurl = '/#/app/keyselect';
        }
        else {
            $scope.backurl = '/#/home';
        }
    }
]);