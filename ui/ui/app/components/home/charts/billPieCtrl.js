'use strict';

angular.module('trackit.home')


.controller('BillPieCtrl', ['$scope', 'BillModel', '$cookies', '$filter',
    function($scope, BillModel, $cookies, $filter) {

        // Retrieve the data from the model
        BillModel.getBillPie({
            // AWS key Id as parameter for API Call
            id: $cookies.getObject('awsKey')
        }, function(data) {
            if ('message' in data) {
              $scope.awsBillPieNoDataMessage = data['message'];
            } else {
              $scope.awsBillPieNoDataMessage = null;
              $scope.month = data.months[0].month.substr(0, 7);
              $scope.data = data.months[0].products;
              $scope.options = options;
            }
            // update centered title with new bill total
            updateTitle(getPieTotal(data.months[0].products));
        }, function(data) {
            console.log(data);
        });

        // Options for Angular-NVD3 pie chart
        var options = {
            chart: {
                type: 'pieChart',
                height: 350,
                donut: true,
                x: function(d) {
                    return d.product;
                },
                y: function(d) {
                    return d.cost;
                },
                donutRatio: 0.45,
                showLabels: false,
                title: "a",
                pie: {},
                duration: 500,
                legend: {
                    margin: {
                        top: 5,
                        right: 30,
                        bottom: 5,
                        left: 0
                    },
                    dispatch: {
                        stateChange: function(e) {
                            // update title if a serie is disabled so the total in the middle of the chart is updated
                            updateTitle(getNewTotal(e.disabled, $scope.data));
                        }
                    }
                }
            }
        };

        // Get bill total
        function getPieTotal(data) {
            var res = 0;

            for (var i = 0; i < data.length; i++) {
                res += data[i].cost;
            }
            return $filter('number')(res.toFixed(2));
        }

        function getNewTotal(disabled, data) {
            var res = 0;
            for (var i = 0; i < data.length; i++) {
                if (!disabled[i])
                    res += data[i].cost;
            }
            return $filter('number')(res.toFixed(2));
        }

        // Update bill total
        function updateTitle(newTitle) {
            var tmp = options;
            tmp.chart.title = "$" + newTitle;
            $scope.options = tmp;

            // We wait the time of the animation and then refresh the whole directive for the title to update
            setTimeout(function() {
                $scope.api.refresh();
            }, $scope.options.chart.duration);
        }

    }
])
.controller('GCBillPieCtrl', ['$scope', 'BillModel', '$cookies',
    function($scope, BillModel, $cookies) {

        // Retrieve the data from the model
        BillModel.getGCBillPie({
            // AWS key Id as parameter for API Call
            id: $cookies.getObject('gcKey')
        }, function(data) {
            $scope.month = data.month;
            $scope.data = data.products;
            $scope.options = options;
            // update centered title with new bill total
            updateTitle(getPieTotal(data.products));
        }, function(data) {
            console.log(data);
        });

        // Options for Angular-NVD3 pie chart
        var options = {
            chart: {
                type: 'pieChart',
                height: 350,
                donut: true,
                x: function(d) {
                    return d.product;
                },
                y: function(d) {
                    return d.cost;
                },
                donutRatio: 0.45,
                showLabels: false,
                title: "a",
                pie: {},
                duration: 500,
                legend: {
                    margin: {
                        top: 5,
                        right: 30,
                        bottom: 5,
                        left: 0
                    },
                    dispatch: {
                        stateChange: function(e) {
                            // update title if a serie is disabled so the total in the middle of the chart is updated
                            updateTitle(getNewTotal(e.disabled, $scope.data));
                        }
                    }
                }
            }
        };

        // Get bill total
        function getPieTotal(data) {
            var res = 0;

            for (var i = 0; i < data.length; i++) {
                res += data[i].cost;
            }
            console.log(res);
            return res.toFixed(2);
        }

        function getNewTotal(disabled, data) {
            var res = 0;
            for (var i = 0; i < data.length; i++) {
                if (!disabled[i])
                    res += data[i].cost;
            }
            return res.toFixed(2);
        }

        // Update bill total
        function updateTitle(newTitle) {
            var tmp = options;
            tmp.chart.title = "$" + newTitle;
            $scope.options = tmp;

            // We wait the time of the animation and then refresh the whole directive for the title to update
            setTimeout(function() {
                $scope.api.refresh();
            }, $scope.options.chart.duration);
        }

    }
]);
