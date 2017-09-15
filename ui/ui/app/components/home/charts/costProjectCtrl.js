'use strict';

angular.module('trackit.home')
    .controller('GCCostProjectCtrl', ['$scope', 'BillModel', '$cookies',
        function($scope, BillModel, $cookies) {


            function processMonth() {
                $scope.data = $scope.selectedMonth.projects;
                updateTitle(getPieTotal($scope.selectedMonth.projects));
            }


            // Retrieve data for chart
            BillModel.getGCCostProject({
                    // AWS key Id as parameter for API Call
                    id: $cookies.getObject('gcKey')
                },
                function(data) {

                    console.log(data);
                    $scope.months = data.months.months;
                    $scope.selectedMonth = $scope.months[$scope.months.length - 1];
                    $scope.dataLoaded = true;
                    $scope.options = options;

                    processMonth();


                },
                function(data) {
                    console.log(data);
                });

                $scope.$watch('selectedMonth', function(nvalue) {
                  processMonth();
                });


            // Options for Angular-NVD3 pie chart
            var options = {
                chart: {
                    type: 'pieChart',
                    height: 350,
                    donut: true,
                    x: function(d) {
                        return d.project;
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
