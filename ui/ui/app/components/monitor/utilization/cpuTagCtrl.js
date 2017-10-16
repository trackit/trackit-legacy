'use strict';

angular.module('trackit.home')


.controller('cpuTagCtrl', ['$scope', 'BillModel', '$cookies',
    function($scope, BillModel, $cookies) {

        $scope.toggle = true;
        $scope.tagWithNoData = false;

        BillModel.getTagsOnlyWithData({
            id: $cookies.getObject('awsKey')
        }, function(data) {
            if ('message' in data) {
                $scope.awsCPUTagNoDataMessage = data['message'];
            } else {
                $scope.awsCPUTagNoDataMessage = null;
                $scope.tags = data.tags;

                BillModel.getTags({
                    id: $cookies.getObject('awsKey')
                }, function(data2) {
                    if (data.tags.length !== data2.tags.length) {
                        $scope.tagWithNoData = true;
                    }
                }, function(data2) {
                    console.log(data2);
                });

                $scope.selectTag($scope.tags[0]);
                setTimeout(() => {
                    window.dispatchEvent(new Event('resize'));
                }, 1000);
            }
        }, function(data) {
            console.log(data);
        });

        $scope.$watch('selectedTag', function(newValue, oldValue) {
            if (newValue) {
                BillModel.getCPUTagHourly({
                    id: $cookies.getObject('awsKey'),
                    tag: newValue
                }, function(data) {
                    var cpuUsageHour = [];
                    var cpu = {};
                    cpu.values = [];

                    for (var j = 0; j < data.values.length; j++) {
                        var tmpValue = data.values[j];
                        cpu = {};
                        cpu.values = [];
                        cpu.key = tmpValue.tag_value;

                        for (var i = 0; i < tmpValue.usage.length; i++) {
                            cpu.values.push({
                                x: i,
                                y: tmpValue.usage[i].cpu
                            });
                        }
                        cpuUsageHour.push(cpu);
                    }
                    $scope.cpuUsageHour = cpuUsageHour;
                    if (!$scope.toggle) {
                        $scope.data = $scope.cpuUsageHour;
                        $scope.data.length >= 10 ? $scope.moreThanTen = true : $scope.moreThanTen = false;

                    }
                    setTimeout(() => {
                        window.dispatchEvent(new Event('resize'));
                    }, 1000);
                }, function(data) {
                    console.log(data);
                });

                BillModel.getCPUTagDaily({
                    id: $cookies.getObject('awsKey'),
                    tag: newValue
                }, function(data) {
                    var cpuUsageDay = [];
                    var cpu = {};
                    cpu.values = [];

                    for (var j = 0; j < data.values.length; j++) {
                        var tmpValue = data.values[j];
                        cpu = {};
                        cpu.values = [];
                        cpu.key = tmpValue.tag_value;

                        for (var i = 0; i < tmpValue.usage.length; i++) {
                            cpu.values.push({
                                x: i,
                                y: tmpValue.usage[i].cpu
                            });
                        }
                        cpuUsageDay.push(cpu);
                    }
                    $scope.cpuUsageDay = cpuUsageDay;

                    if ($scope.toggle) {
                        $scope.data = $scope.cpuUsageDay;
                        $scope.data.length >= 10 ? $scope.moreThanTen = true : $scope.moreThanTen = false;

                    }
                     setTimeout(() => {
                        window.dispatchEvent(new Event('resize'));
                    }, 1000);
                }, function(data) {
                    console.log(data);
                });

            }
        });

        $scope.selectTag = function(tag) {
            $scope.selectedTag = tag;
        }



        var days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
        var hours = ["12:00 AM", "01:00 AM", "02:00 AM", "03:00 AM", "04:00 AM", "05:00 AM", "06:00 AM", "07:00 AM", "08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM",
            "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM", "07:00 PM", "08:00 PM", "09:00 PM", "10:00 PM", "11:00 PM"
        ];

        $scope.onChange = function() {
            if ($scope.toggle) {
                $scope.data = $scope.cpuUsageHour;
                $scope.toggle = false;
            } else {
                $scope.data = $scope.cpuUsageDay;
                $scope.toggle = true;
            }
        };

        $scope.options = {
            chart: {
                type: 'lineChart',
                height: 500,
                margin: {
                    top: 30,
                    right: 75,
                    bottom: 50,
                    left: 75
                },
                x: function(d) {
                    return d.x;
                },
                y: function(d) {
                    return d.y;
                },
                useInteractiveGuideline: true,
                xAxis: {
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
        };
    }
]);
