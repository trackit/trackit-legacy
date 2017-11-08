'use strict';

angular.module('trackit.prediction')


.controller('PredictionCtrl', ['$scope', '$uibModal', 'SuggestionsModel', 'AWSKey', '$cookies',
        function($scope, $uibModal, SuggestionsModel, AWSKey, $cookies) {

            var awsSelectedKey = $cookies.getObject('awsKey');

            $scope.openPricingOptions = function() {

                var modalInstance = $uibModal.open({
                    animation: $scope.animationsEnabled,
                    templateUrl: 'components/optimize/prediction/pricingOptionsModal.html',
                    controller: 'PricingOptionsCtrl',
                    size: 'lg'
                });
            };

            var tk = AWSKey.query({}, function() {
                $scope.keys = tk;
                $scope.keySelected = true;
                console.log($scope.keys.accounts.length);
                if (!$scope.keys.accounts.length) {
                    $scope.keyExist = false;
                    $scope.showData = false;
                } else {
                    $scope.keyExist = true;
                    if (awsSelectedKey) {
                        $scope.keySelected = true;
                    } else
                        $scope.keySelected = false;
                }
            });

            if (awsSelectedKey) {
                SuggestionsModel.getUnderutilized({
                        id: awsSelectedKey
                    },
                    function(data) {
                        $scope.underutilized = data.resources;
                    },
                    function(data) {
                        console.log(data);
                    }
                );

                SuggestionsModel.getOndemandSwitch({
                        id: awsSelectedKey
                    },
                    function(data) {
                        $scope.ondemandSwitch = data.on_demand_instances;
                    },
                    function(data) {
                        console.log(data);
                    });

                SuggestionsModel.getAvailableVolumes({
                        id: awsSelectedKey
                    },
                    function(data) {
                        $scope.availableVolumes = data.volumes;
                    },
                    function(data) {
                        console.log(data);
                    });

                SuggestionsModel.getStoppedInstances({
                        id: awsSelectedKey
                    },
                    function(data) {
                        $scope.stoppedInstances = data.total;
                    },
                    function(data) {
                        console.log(data);
                    });


            }
            else {
                $scope.keySelected = false;
            }


        }
    ])
    .controller('PricingOptionsCtrl', ['$scope', 'EstimationModel', '$cookies', '$uibModalInstance',
        function($scope, EstimationModel, $cookies, $uibModalInstance) {

            $scope.selectedPricing = 0;


            function capitalizeFirstLetter(string) {
                if (string)
                    return string.charAt(0).toUpperCase() + string.slice(1);
            }

            function getCount(pricingOpt) {
                if (pricingOpt)
                    for (var i = 0; i < pricingOpt.length; i++) {
                        if (pricingOpt[i].count)
                            return pricingOpt[i].count;
                    }
            }

            // return ondemand current pricing
            function getCurrentPrice(pricingOpt) {
                if (pricingOpt)
                    for (var i = 0; i < pricingOpt.length; i++) {
                        if (pricingOpt[i].type == 'ondemand')
                            return pricingOpt[i].costPerHour;
                    }
            }

            // returned save calculated percent
            function getSavePercent(reserved, ondemand) {
                return 100 - ((reserved * 100) / ondemand);
            }

            // get monthly pricing for current on demand instance
            function getCurrentMonth(pricingOpt) {
                if (pricingOpt)
                    for (var i = 0; i < pricingOpt.length; i++) {
                        if (pricingOpt[i].type == 'ondemand')
                            return pricingOpt[i].months;
                    }
            }

            // get a specific cost for a specific month
            function getPriceMonth(month, arr) {
                for (var i = 0; i < arr.length; i++) {
                    if (arr[i].month == month)
                        return arr[i].cost;
                }
            }

            // returns the table for comparison display
            function getComparisonTable(currentMonths, estimatedMonths) {
                console.log(currentMonths);
                console.log(estimatedMonths);
                if (currentMonths && estimatedMonths) {
                    console.log('b');
                    var res = currentMonths;

                    for (var i = 0; i < res.length; i++) {
                        res[i].estimatedCost = getPriceMonth(res[i].month, estimatedMonths);
                    }
                    console.log(res);
                    return res;
                }
            }

            $scope.getComparisonTable = getComparisonTable;
            $scope.getSavePercent = getSavePercent;
            $scope.getCurrentPrice = getCurrentPrice;
            $scope.getCount = getCount;

            $scope.selectPricing = function(index) {
                $scope.selectedPricing = index;
            };

            $scope.close = function() {
                $uibModalInstance.close();
            };

            $scope.capitalizeFirstLetter = capitalizeFirstLetter;

            $scope.$watch('selectedType', function(newValue, oldValue) {
                if ($scope.data) {
                    $scope.pricing = newValue;
                    $scope.currentMonths = getCurrentMonth($scope.pricing.pricing_options);
                    $scope.selectedPricing = 0;
                }
            });


            EstimationModel.getPrediction({
                id: $cookies.getObject('awsKey')
            }, function(data) {
                $scope.data = data;
                $scope.instanceTypes = data.instances;
                $scope.dataLoaded = true;
                console.log(data);
            }, function(data) {
                console.log(data);
            });
        }
    ]);
