'use strict';

angular.module('trackit')

    .controller('RequestTrialCtrl', ['$scope', '$http', 'apiBaseUrl', '$state', 'Config', '$cookies', '$timeout', '$location', '$stateParams',
        function($scope, $http, apiBaseUrl, $state, Config, $cookies, $timeout, $location, $stateParams) {

            $scope.demoMode = $stateParams.demo;
            $scope.showForm = true;

            $scope.companySizes = [
                "Less than 100",
                "101 - 1000",
                "More than 1000"
            ];

            $scope.cloudProviders = [{
                    label: "AWS",
                    checked: false,
                    iconUrl: 'img/s3-square.png',
                },
                {
                    label: "Google Cloud Platform",
                    checked: false,
                    iconUrl: 'img/gc-square.png',
                },
                {
                    label: "Microsoft Azure",
                    checked: false,
                    iconUrl: 'img/ms-square.png',
                }
            ];


            $scope.cloudConcerns = [{
                    checked: false,
                    label: "Cost visibility",
                },
                {
                    checked: false,
                    label: "Regulatory compliance",
                },
                {
                    checked: false,
                    label: "Utilization",
                },
                {
                    checked: false,
                    label: "Data management across multiple cloud platforms",
                },
                {
                    checked: false,
                    label: "Security",
                },
            ];




            function optionsToString(options) {
                var res = [];
                for (var i = 0; i < options.length; i++) {
                    if (options[i].checked) {
                        res.push(options[i].label);
                    }
                }
                return res;
            }

            $scope.submitForm = function() {
                var params = {
                    g_recaptcha_response: $scope.user.captcha,
                    name: $scope.user.firstName + ' ' + $scope.user.lastName,
                    email: $scope.user.email,
                    which_cloud: optionsToString($scope.cloudProviders),
                    cloud_concerns: optionsToString($scope.cloudConcerns),
                };
                if ($scope.user.phone_number) {
                    params.phone_number = $scope.user.phone_number;
                }
                if ($scope.user.company_name) {
                    params.company_name = $scope.user.company_name;
                }
                if ($scope.user.employees) {
                    params.employees = $scope.user.employees;
                }

                $http({
                    method: 'POST',
                    url: apiBaseUrl + '/prospect/' + (($scope.demoMode) ? 'demo' : 'trial'),
                    data: params
                }).then(function(res) {
                    $scope.done = true;
                    console.log(res);
                }, function(res) {
                    $scope.error = true;
                    console.log(res);
                });

            };

        }
    ]);
