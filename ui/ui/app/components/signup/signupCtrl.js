'use strict';

angular.module('trackit')

.controller('SignupCtrl', ['$scope', '$http', 'apiBaseUrl', '$state', 'Config', '$cookies', '$timeout', '$location', '$anchorScroll',
  function($scope, $http, apiBaseUrl, $state, Config, $cookies, $timeout, $location, $anchorScroll) {
    $scope.errorFields = {};
    $scope.successRegister = false;

    $scope.signUp = function() {
      if ($scope.password !== $scope.password2) {
        $scope.errorFields.password2 = ["Password confirmation must match"];
        return;
      }

      $http({
        method: 'POST',
        url: apiBaseUrl + '/signup',
        data: {
          email: $scope.email,
          firstname: $scope.firstname,
          lastname: $scope.lastname,
          password: $scope.password
        }
      }).then(function(res) {
        $scope.errorFields = {};
        $scope.unknownError = false;
        $scope.successRegister = true;
        $location.hash('success-register');
        $anchorScroll();
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
            $timeout(function(){ $state.go('app.keyselect', {fromLogin: true});}, 5000);
          });
        //$state.go('login');
      }, function(res) {
        if (res.data && res.data.fields) {
          $scope.errorFields = res.data.fields;
        } else {
          $scope.unknownError = true;
        }
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
]);
