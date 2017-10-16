'use strict';

angular.module('trackit')
    .controller('UtilizationCtrl', ['$scope', 'AWSKey', '$cookies',
        function($scope, AWSKey, $cookies) {

            $scope.awsSelectedKey = $cookies.getObject('awsKey');
            $scope.gcSelectedKey = $cookies.getObject('gcKey');

            if ($scope.awsSelectedKey) {
                // Retrieve key and assure that data is already processed. if not display a spinner by setting showData to false
                let tk = AWSKey.query({}, function () {
                    $scope.keys = tk;
                    $scope.tmp = $scope.keys.accounts.length;
                    $scope.keySelected = true;
                    if (!$scope.keys.accounts.length) {
                        $scope.keyExist = false;
                        $scope.showData = false;
                    } else {
                        $scope.keyExist = true;
                        if ($scope.awsSelectedKey) {
                            $scope.keySelected = true;
                            $scope.showData = true;
                        } else {
                            $scope.keySelected = false;
                        }
                    }
                });
            }
            if ($scope.gcSelectedKey) {
                /* TODO for now we asssume data for GC are ready */
                $scope.keyExist = true;
                $scope.keySelected = true;
                $scope.showData = true;
                $scope.dataReady = true;
            }

            $scope.activeTab = 1;

            $scope.changeTab = (tab) => {
                $scope.activeTab = tab;
                setTimeout(() => {
                    window.dispatchEvent(new Event('resize'));
                }, 1000);
            }

        }]);
