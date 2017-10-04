'use strict';

angular.module('trackit')

.controller('LoginCtrl', ['$scope', '$http', 'apiBaseUrl', '$state', '$cookies', 'Config', '$uibModal',
    function($scope, $http, apiBaseUrl, $state, $cookies, Config, $uibModal) {
        $scope.enableForgottenPassword = Config.enableForgottenPassword == "True";
        $scope.onlyEmail = Config.loginOnlyEmail == "True";
        $scope.emailType = ($scope.onlyEmail ? "email" : "text");
        $scope.emailName = "Email" + ($scope.onlyEmail ? "" : " or username")
        $scope.login = function() {
            $http({
                method: 'POST',
                url: apiBaseUrl + '/login',
                data: {
                    email: $scope.email,
                    password: $scope.password
                }
            }).then(function(res) {
                $scope.invalidCredentials = false;
                var expires = new Date();
                expires.setDate(expires.getDate() + 2);
                $cookies.putObject('userToken', res.data, {
                    expires: expires
                });
                /* Sending fromLogin so keyselect redirect to home if cookies are set */
                $state.go('app.keyselect', {fromLogin: true});
            }, function(res) {
                $scope.invalidCredentials = true;
            });
        };

        $scope.openForgottenPasswordModal = function() {
            var modalInstance = $uibModal.open({
                templateUrl: 'components/login/forgotPasswordModal.html',
                controller: 'ForgottenPasswordCtrl'
            });

            modalInstance.result.then(function(selectedItem) {
                $scope.selected = selectedItem;
            }, function() {
                //$log.info('Modal dismissed at: ' + new Date());
            });
        };


        $scope.authenticate = function(provider) {
            switch (provider) {
                case 'google':
                    window.location.assign(Config.apiUrl('/auth/google/initiate'));
                    break;
                default:
            }
        }
    }
])

.controller('ForgottenPasswordCtrl', ['$scope', '$http', 'apiBaseUrl', 'Config', '$uibModalInstance',
    function($scope, $http, apiBaseUrl, Config, $uibModalInstance) {

      $scope.close = function() {
        $uibModalInstance.dismiss('cancel');
      };

      $scope.submit = function() {
          $http({
              method: 'POST',
              url: apiBaseUrl + '/lostpassword',
              data: {
                  email: $scope.email
              }
          }).then(function(res) {
              $scope.done = true;
              $scope.email = "";
              console.log(res);
          }, function(res) {
              $scope.done = true;
              $scope.email = "";
              console.log(res);
          });
      };

    }
])

.controller('ResetPasswordCtrl', ['$scope', '$http', 'apiBaseUrl', 'Config', '$stateParams',
    function($scope, $http, apiBaseUrl, Config, $stateParams) {

      var token = $stateParams.token;

      $scope.reset = function() {
          $http({
              method: 'POST',
              url: apiBaseUrl + '/changelostpassword',
              data: {
                  lost_password: token,
                  password: $scope.password
              }
          }).then(function(res) {
              $scope.success = true;
              console.log(res);
          }, function(res) {
              $scope.error = true;
              console.log(res);
          });
      };

    }
]);
