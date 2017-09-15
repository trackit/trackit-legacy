'use strict';

angular.module('trackit.statistics')

    .controller('AWSBandwidthCtrl', ['$scope', 'BillModel', '$cookies', '$filter',
        function($scope, BillModel, $cookies, $filter) {

            var orderBy = $filter('orderBy');

            $scope.currentPage = 1;
            $scope.pageSize = 10;

            $scope.aws_services = [];
            $scope.dataLoaded = false;

            BillModel.getEC2BandwidthCost({
                    id: $cookies.getObject('awsKey')
                },
                function(data) {
                    if ('message' in data) {
                        $scope.aws_services.push({
                            name: 'EC2',
                            message: data['message']
                        });
                    } else {
                        $scope.aws_services.push({
                            name: 'EC2',
                            total_cost: data['total_cost'],
                            total_gb: data['total_gb'],
                            transfers: data['transfers']
                        });
                    }
                    BillModel.getS3BandwidthCost({
                            id: $cookies.getObject('awsKey')
                        },
                        function(data) {
                            if ('message' in data) {
                                $scope.aws_services.push({
                                    name: 'S3',
                                    message: data['message']
                                });
                            } else {
                                $scope.aws_services.push({
                                    name: 'S3',
                                    total_cost: data['total_cost'],
                                    total_gb: data['total_gb'],
                                    transfers: data['transfers']
                                });
                            }
                            $scope.dataLoaded = true;
                        });
                });

            $scope.selectService = function(service) {
              $scope.predicate = null;
              $scope.reverse = null;
              $scope.countUp = null;
              $scope.selectedService = service;
              $scope.order('cost');
              $scope.chartData = $scope.selectedService.transfers;
            }

            $scope.order = function(predicate) {
                $scope.predicate = predicate;
                $scope.reverse = ($scope.predicate === predicate) ? !$scope.reverse : false;
                $scope.selectedService.transfers = orderBy($scope.selectedService.transfers, predicate, $scope.reverse);
            };

            $scope.chartOptions = {
                chart: {
                    type: 'pieChart',
                    height: 450,
                    donut: true,
                    x: function(d) {
                        return d.type;
                    },
                    y: function(d) {
                        return d.cost;
                    },
                    showLabels: false,
                    showLegend: false,
                    valueFormat: function(n) {
                        return ('$' + n.toFixed(2));
                    },
                    duration: 500,
                    legend: {
                        margin: {
                            top: 5,
                            right: 70,
                            bottom: 5,
                            left: 0
                        }
                    }
                }
            };
        }
    ]);
