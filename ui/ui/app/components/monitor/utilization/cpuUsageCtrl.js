'use strict';

angular.module('trackit.home')

    .controller('cpuUsageCtrl', ['$scope', 'BillModel', '$cookies',
        function($scope, BillModel, $cookies) {

            BillModel.getCpuUsageDay({
                // AWS key Id as parameter for API Call
                id: $cookies.getObject('awsKey')
            }, function(data) {
                if ('message' in data) {
                  $scope.awsCPUUsageNoDataMessage = data['message'];
                } else {
                  $scope.awsCPUUsageNoDataMessage = null;
                  var cpuUsageDay = [];
                  var cpu = {};
                  cpu.key = "CPU Usage";
                  cpu.values = [];

                  for (var i = 0; i < data.hours.length; i++) {
                      cpu.values.push({
                          label: data.hours[i].day,
                          x: i,
                          y: data.hours[i].cpu
                      });
                  }
                  cpuUsageDay.push(cpu);
                  $scope.cpuUsageDay = cpuUsageDay;
                  $scope.data = $scope.cpuUsageDay;
                }
            });

            BillModel.getCpuUsageHour({
                // AWS key Id as parameter for API Call
                id: $cookies.getObject('awsKey')
            }, function(data) {
                var cpuUsageHour = [];
                var cpu = {};
                cpu.key = "CPU Usage";
                cpu.values = [];

                for (var i = 0; i < data.hours.length; i++) {
                    cpu.values.push({
                        label: data.hours[i].hour,
                        x: i,
                        y: data.hours[i].cpu
                    });
                }
                cpuUsageHour.push(cpu);
                $scope.cpuUsageHour = cpuUsageHour;
            });

            $scope.toggle = true;

            $scope.onChange = function() {
                if ($scope.toggle) {
                    $scope.data = $scope.cpuUsageHour;
                    $scope.toggle = false;
                    $scope.options = getChartOptions();
                } else {
                    $scope.data = $scope.cpuUsageDay;
                    $scope.toggle = true;
                    $scope.options = getChartOptions();
                }
            };

            var days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
            var hours = ["12:00 AM", "01:00 AM", "02:00 AM", "03:00 AM", "04:00 AM", "05:00 AM", "06:00 AM", "07:00 AM", "08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM",
                "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM", "07:00 PM", "08:00 PM", "09:00 PM", "10:00 PM", "11:00 PM"
            ];

            function getForceX() {
                if ($scope.toggle) {
                    return [-0.5, 6.5];
                } else {
                    return [-0.5, 24];
                }
            }

            function getChartOptions() {
                return ({
                    chart: {
                        type: 'historicalBarChart',
                        height: 443.5,
                        margin: {
                            top: 30,
                            right: 75,
                            bottom: 50,
                            left: 75
                        },
                        bars: {
                            forceY: [0],
                            forceX: getForceX()
                        },
                        x: function(d) {
                            return d.x;
                        },
                        y: function(d) {
                            return d.y;
                        },
                        useInteractiveGuideline: true,
                        xAxis: {
                            axisLabel: 'Day',
                            tickFormat: function(d) {
                                if ($scope.toggle)
                                    return days[d];
                                else
                                    return hours[d];
                            }
                        },
                        yAxis: {
                            axisLabel: 'CPU Usage (%)',
                            tickFormat: function(d) {
                                return d3.format(',.2f')(d)
                            }
                        }
                    }
                });
            }

            $scope.options = getChartOptions();
        }
    ]);
