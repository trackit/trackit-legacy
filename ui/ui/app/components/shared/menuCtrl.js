'use strict';

angular.module('trackit.menu', [])


.controller('MenuCtrl', ['$scope', '$rootScope', '$state', 'apiBaseUrl', '$http', '$cookies', 'Config', '$uibModal',
        function($scope, $rootScope, $state, apiBaseUrl, $http, $cookies, Config, $uibModal) {

            var awsSelectedKey = $cookies.getObject('awsKey');
            var gcSelectedKey = $cookies.getObject('gcKey');
            $scope.awsSelectedKey = awsSelectedKey;
            $scope.gcSelectedKey = gcSelectedKey;

            /* Refresh provider states on key change (fired from keyselect controller) */
            $scope.$on('keysChanged', function(event) {
                console.log('Menu : key change detected');
                awsSelectedKey = $cookies.getObject('awsKey');
                gcSelectedKey = $cookies.getObject('gcKey');
                $scope.awsSelectedKey = awsSelectedKey;
                $scope.gcSelectedKey = gcSelectedKey;
            });

            $scope.openEditUser = function() {
                var modalInstance = $uibModal.open({
                    ariaLabelledBy: 'modal-title',
                    ariaDescribedBy: 'modal-body',
                    templateUrl: 'components/shared/editUserModal.html',
                    controller: 'EditUserCtrl'
                });

                modalInstance.result.then(function(selectedItem) {
                    $http.get(Config.apiUrl("/user")).then(function(data) {
                        $scope.user = data.data;
                    });
                }, function() {
                    $log.info('Modal dismissed at: ' + new Date());
                });
            };

            $scope.currentState = $state.current.name;

            // Update currentState for navbar active class
            $rootScope.$on('$stateChangeStart',
                function(event, toState, toParams, fromState, fromParams) {
                    $scope.currentState = toState.name;
                    console.log($scope.currentState);
                });


            $http.get(Config.apiUrl("/user")).then(function(data) {
                $scope.user = data.data;
            });

            Object.defineProperty($scope, 'awsKey', {
                get: function() {
                    return $rootScope.awsKey
                }
            });

            $scope.logout = function() {
                $http.get(apiBaseUrl + '/logout');
                $rootScope.userToken = null;
                $cookies.remove('userToken');
                document.location.href = ""
            };
        }
    ])
    .controller('EditUserCtrl', ['$scope', '$rootScope', '$state', 'apiBaseUrl', '$http', '$cookies', 'Config', '$uibModalInstance',
        function($scope, $rootScope, $state, apiBaseUrl, $http, $cookies, Config, $uibModalInstance) {
            console.log('good');

            $http({
                method: 'GET',
                url: apiBaseUrl + '/user'
            }).then(function(res) {
                console.log(res);
                $scope.user = res.data;
                $scope.dataLoaded = true;
            }, function(res) {
                //$scope.invalidCredentials = true;
            });

            $scope.submit = function() {
                var requestData = {};
                if ($scope.user.firstname && $scope.user.firstname.length) {
                    requestData.firstname = $scope.user.firstname;
                }
                if ($scope.user.lastname && $scope.user.lastname.length) {
                    requestData.lastname = $scope.user.lastname;
                }
                if ($scope.user.email && $scope.user.email.length) {
                    requestData.email = $scope.user.email;
                }
                if ($scope.user.password && $scope.user.password.length) {
                    requestData.password = $scope.user.password;
                }

                $http({
                    method: 'PUT',
                    url: apiBaseUrl + '/user',
                    data: requestData
                }).then(function(res) {
                    console.log(res);
                    $uibModalInstance.close();
                }, function(res) {
                  $scope.errorFields = res.data.fields;
                });

            }

        }
    ]);
