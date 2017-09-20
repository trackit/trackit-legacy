'use strict';

var module = angular.module('trackit.home');

module.controller('HomeCtrl', ['$scope', '$http', 'Config', 'AWSKey', '$cookies',
    function($scope, $http, Config, AWSKey, $cookies) {


        var awsSelectedKey = $cookies.getObject('awsKey');
        var gcSelectedKey = $cookies.getObject('gcKey');
        $scope.awsSelectedKey = awsSelectedKey;
        $scope.gcSelectedKey = gcSelectedKey;


        if (awsSelectedKey) {
            // Retrieve key and assure that data is already processed. if not display a spinner by setting showData to false
            var tk = AWSKey.query({}, function() {
                $scope.keys = tk;
                $scope.tmp = $scope.keys.accounts.length;
                $scope.keySelected = true;
                if (!$scope.keys.accounts.length) {
                    $scope.keyExist = false;
                    $scope.showData = false;
                } else {
                    $scope.keyExist = true;
                    if (awsSelectedKey) {
                        $scope.keySelected = true;
                        $scope.showData = true;
                    } else {
                        $scope.keySelected = false;
                    }
                }
            });
        }
        if (gcSelectedKey) {
            /* TODO for now we asssume data for GC are ready */
            $scope.keyExist = true;
            $scope.keySelected = true;
            $scope.showData = true;
            $scope.dataReady = true;

        }

      $scope.toggleReservedDetails = function() {
        $scope.show_reserved_report = !$scope.show_reserved_report;
      };


      $scope.getFormattedDateFromUnixTimestamp = function(timestamp) {
          var tmp = new Date(timestamp*1000);
          return tmp.toLocaleString();
      };

    }
]);
