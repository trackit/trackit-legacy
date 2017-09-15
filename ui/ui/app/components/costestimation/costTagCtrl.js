'use strict';

angular.module('trackit.statistics')

    .controller('CostTagCtrl', ['$scope', 'BillModel', '$cookies', '$filter',
        function($scope, BillModel, $cookies, $filter) {

            $scope.currentPage = 1;
            $scope.pageSize = 10;

            var orderBy = $filter('orderBy');


            $scope.order = function(predicate) {
                $scope.predicate = predicate;
                $scope.reverse = ($scope.predicate === predicate) ? !$scope.reverse : false;
                $scope.selectedMonth.tags = orderBy($scope.selectedMonth.tags, predicate, $scope.reverse);
            };

            $scope.setSelectedMonth = function(month) {
                    $scope.selectedMonth = month;

                    $scope.numberOfPages = function() {
                        return Math.ceil(month.tags.length / $scope.pageSize);
                    }
                    $scope.chartData = month.tags;
                    $scope.reverse = false;
                    $scope.order('cost');


            }

            function getLatestMonth(months) {
                return months[months.length - 1];
            }



           $scope.$watch('selectedTag', function(newValue, oldValue) {
                if (newValue) {

                    $scope.predicate = null;
                    $scope.reverse = null;
                    $scope.countUp = null;

                    BillModel.getTagDetails({
                            id: $cookies.getObject('awsKey'),
                            tag: newValue
                        },
                        function(data) {
                            $scope.tagMonths = data.months;
                            $scope.selectedMonth = getLatestMonth($scope.tagMonths);
                            $scope.scopeSelectedMonth = getLatestMonth($scope.tagMonths);
                            $scope.order('cost');
                            $scope.chartData = $scope.selectedMonth.tags;
                        },
                        function(data) {
                            console.log(data);
                        });

                }
            });

            BillModel.getTags({
                    id: $cookies.getObject('awsKey')
                },
                function(data) {
                    console.log(data);
                    if ('message' in data) {
                        $scope.awsCostTagNoDataMessage = data['message'];
                        $scope.dataLoaded = false;
                    } else {
                        $scope.awsCostTagNoDataMessage = null;
                        $scope.dataLoaded = true;
                        $scope.tags = data.tags;
                        $scope.selectedTag = $scope.tags[0];
                    }
                },
                function(data) {
                    console.log(data);
                });

            $scope.selectTag = function(tag) {
                $scope.tagMonths = null;
                $scope.selectedMonth = null;
                $scope.selectedTag = tag;
            }


            $scope.chartOptions = {
                chart: {
                    type: 'pieChart',
                    height: 450,
                    donut: true,
                    x: function(d) {
                        return d.tag_value;
                    },
                    y: function(d) {
                        return d.cost;
                    },
                    showLabels: true,
                    showLegend: false,

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
