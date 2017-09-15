'use strict';

angular.module('trackit.home')


.controller('CostUsageCtrl', ['$scope', 'BillModel', '$cookies',
    function($scope, BillModel, $cookies) {

        // Retrieve data for chart
        BillModel.getCUCostUsage({
                // AWS key Id as parameter for API Call
                id: $cookies.getObject('awsKey')
            },
            function(data) {
                if ('message' in data) {
                  $scope.awsCostUsageNoDataMessage = data['message'];
                } else {
                  $scope.awsCostUsageNoDataMessage = null;
                  var chartData = [];
                  var cost = {};
                  var usage = {};

                  cost.yAxis = 1;
                  cost.key = "Price";
                  cost.values = [];
                  cost.bar = true;

                  usage.bar = false;
                  usage.yAxis = 2;
                  usage.key = "CPU Usage";
                  usage.values = [];

                  // Filling usage and cost with corresponding values
                  for (var i = 0; i < data.days.length; i++) {
                      var costValue = {
                          x: data.days[i].day
                      };
                      var usageValue = {
                          x: data.days[i].day
                      };

                      costValue.y = data.days[i].cost;
                      usageValue.y = data.days[i].cpu;

                      cost.values.push(costValue);
                      usage.values.push(usageValue);

                  }
                  chartData.push(usage);
                  chartData.push(cost);

                  // Setting retrieved data to scope binding
                  $scope.data = chartData;
                }
            },
            function(data) {
                console.log(data);
            });


        // Cost and usage Angular-NVD3 options (line + bar chart with focus)
        $scope.options = {
            chart: {
                type: 'linePlusBarChart',
                height: 500,
                margin: {
                    top: 30,
                    right: 75,
                    bottom: 50,
                    left: 75
                },
                useInteractiveGuideline: true,
                bars: {
                    forceY: [0]
                },
                bars2: {
                    forceY: [0]
                },
                //color: ['#2ca02c', 'darkred'],
                x: function(d, i) {
                    return i
                },
                xAxis: {
                    // Main X axis
                    axisLabel: 'Day',
                    tickFormat: function(d) {
                        var dx = $scope.data[0].values[d] && $scope.data[0].values[d].x || 0;
                        if (dx) {
                            var parts = dx.split('-').map(function(v) {
                                return parseInt(v, 10);
                            });
                            return d3.time.format('%x')(new Date(parts[0], parts[1] - 1, parts[2]))

                        }
                    }
                },
                x2Axis: {
                    // Focus X Axis
                    tickFormat: function(d) {
                        var dx = $scope.data[0].values[d] && $scope.data[0].values[d].x || 0;
                        if (dx) {
                            var parts = dx.split('-').map(function(v) {
                                return parseInt(v, 10);
                            });
                            return d3.time.format('%x')(new Date(parts[0], parts[1] - 1, parts[2]))
                        }
                    },
                    showMaxMin: false
                },
                y1Axis: {
                    // Left Y Axis
                    axisLabel: 'Price ($)',
                    tickFormat: function(d) {
                        return '' + d3.format(',.2f')(d);
                    },
                    axisLabelDistance: 12
                },
                y2Axis: {
                    // Right Y Axis
                    axisLabel: 'CPU usage (%)',
                    tickFormat: function(d) {
                        return d3.format(',.2f')(d)
                    }
                }
            }
        };

    }
])
.controller('GCCostUsageCtrl', ['$scope', 'BillModel', '$cookies',
    function($scope, BillModel, $cookies) {

        // Retrieve data for chart
        BillModel.getGCCostUsage({
                // AWS key Id as parameter for API Call
                id: $cookies.getObject('gcKey')
            },
            function(data) {
                var chartData = [];
                var cost = {};
                var usage = {};

                cost.yAxis = 1;
                cost.key = "Price";
                cost.values = [];
                cost.bar = true;

                usage.bar = false;
                usage.yAxis = 2;
                usage.key = "CPU Usage";
                usage.values = [];

                // Filling usage and cost with corresponding values
                for (var i = 0; i < data.days.length; i++) {
                    var costValue = {
                        x: data.days[i].day
                    };
                    var usageValue = {
                        x: data.days[i].day
                    };

                    costValue.y = data.days[i].cost;
                    usageValue.y = data.days[i].cpu;

                    cost.values.push(costValue);
                    usage.values.push(usageValue);

                }
                chartData.push(usage);
                chartData.push(cost);

                console.log(chartData);
                // Setting retrieved data to scope binding
                $scope.data = chartData;


            },
            function(data) {
                console.log(data);
            });


        // Cost and usage Angular-NVD3 options (line + bar chart with focus)
        $scope.options = {
            chart: {
                type: 'linePlusBarChart',
                height: 500,
                margin: {
                    top: 30,
                    right: 75,
                    bottom: 50,
                    left: 75
                },
                useInteractiveGuideline: true,
                bars: {
                    forceY: [0]
                },
                bars2: {
                    forceY: [0]
                },
                //color: ['#2ca02c', 'darkred'],
                x: function(d, i) {
                    return i
                },
                xAxis: {
                    // Main X axis
                    axisLabel: 'Day',
                    tickFormat: function(d) {
                        var dx = $scope.data[0].values[d] && $scope.data[0].values[d].x || 0;
                        if (dx) {
                            var parts = dx.split('-').map(function(v) {
                                return parseInt(v, 10);
                            });
                            return d3.time.format('%x')(new Date(parts[0], parts[1] - 1, parts[2]))

                        }
                    }
                },
                x2Axis: {
                    // Focus X Axis
                    tickFormat: function(d) {
                        var dx = $scope.data[0].values[d] && $scope.data[0].values[d].x || 0;
                        if (dx) {
                            var parts = dx.split('-').map(function(v) {
                                return parseInt(v, 10);
                            });
                            return d3.time.format('%x')(new Date(parts[0], parts[1] - 1, parts[2]))
                        }
                    },
                    showMaxMin: false
                },
                y1Axis: {
                    // Left Y Axis
                    axisLabel: 'Price ($)',
                    tickFormat: function(d) {
                        return '' + d3.format(',.2f')(d);
                    },
                    axisLabelDistance: 12
                },
                y2Axis: {
                    // Right Y Axis
                    axisLabel: 'CPU usage (%)',
                    tickFormat: function(d) {
                        return d3.format(',.2f')(d)
                    }
                }
            }
        };

    }
]);
