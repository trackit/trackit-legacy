'use strict';

angular.module('trackit.statistics')
    .controller('CostResourceCtrl', ['$scope', 'BillModel', '$cookies',
        function($scope, BillModel, $cookies) {

            $scope.dataLoaded = false;

            // This has to be kept up to date if cost by resource changes tab index in the parent scope
            // it is used to know when to flush data to not overload the browser memory
            var currentTabIndex = 3;

            $scope.$on('tabDeselected', function(event, tabIndex) {
                if (tabIndex == currentTabIndex) {
                    console.log('empty cost by resource data');
                    $scope.monthData = null;
                    $scope.searchPool = null;
                    $scope.selectedMonth = null;
                    $scope.dataLoaded = false;
                }
            });

            $scope.$on('tabSelected', function(event, tabIndex) {
                console.log('SELECTED');
                BillModel.getCostResourceMonths({
                        id: $cookies.getObject('awsKey')
                    },
                    function(data) {
                        if ('message' in data) {
                          $scope.awsCostResourceMonthsNoDataMessage = data['message'];
                        } else {
                          $scope.awsCostResourceMonthsNoDataMessage = null;
                          $scope.months = data.months;
                          $scope.selectedMonth = $scope.months[$scope.months.length - 1];
                        }
                    },
                    function(data) {
                        console.log(data);
                    });
            });




            $scope.countUpOptions = {  
                useEasing: true,
                  useGrouping: true,
                  separator: ',',
                  decimal: '.',
                  prefix: 'Month total : $',
                  suffix: ''
            };

            function parseMonthChart(month) {
                var res = [];

                for (var key in month.categories) {
                    if (month.categories.hasOwnProperty(key)) {
                        var tmp = {
                            resource: $scope.getFormattedCatLabel(key),
                            cost: month.categories[key]['total']
                        }
                        res.push(tmp);
                    }
                }

                return res;
            }

            function updateTab(theMonth, theCategoryIndex) {
                $scope.resources = [];
                $scope.tabLoaded = false;
                BillModel.getCostResourceCategory({
                        id: $cookies.getObject('awsKey'),
                        month: theMonth,
                        category: $scope.categories[theCategoryIndex]
                    },
                    function(data) {
                        console.log(data);
                        data.category.resources.sort(function(a, b) {
                            return (a.cost > b.cost) ? -1 : ((b.cost > a.cost) ? 1 : 0);
                        });
                        $scope.resources = data.category.resources;
                        $scope.total = data.category.total;
                        $scope.tabLoaded = true;
                    },
                    function(data) {
                        console.log(data);
                    }
                );

            }

            $scope.$watch('searchResource', function(newValue) {
                if (newValue) {
                    BillModel.getCostResourceSearch({
                            id: $cookies.getObject('awsKey'),
                            month: $scope.selectedMonth,
                            search: newValue
                        },
                        function(data) {
                            console.log(data);
                            $scope.searchPool = data.search_result;
                        },
                        function(data) {
                            console.log(data);
                        }
                    );
                }
            });

            $scope.$watch('selectedTab', function(newValue) {
                if (Number.isInteger(newValue)) {
                    $scope.resources = [];
                    $scope.tabLoaded = false;
                    updateTab($scope.selectedMonth, newValue);
                }
            });

            $scope.$watch('selectedMonth', function(newValue, oldValue) {
                if (newValue) {
                    BillModel.getCostResourceCategories({
                            id: $cookies.getObject('awsKey'),
                            month: newValue
                        },
                        function(data) {
                            $scope.categories = data.categories;
                            $scope.dataLoaded = true;
                            $scope.selectedTab = $scope.categories.length - 1;
                            updateTab($scope.selectedMonth, $scope.selectedTab);

                        },
                        function(data) {
                            console.log(data);
                        }
                    );

                    BillModel.getCostResourceChart({
                            id: $cookies.getObject('awsKey'),
                            month: newValue
                        },
                        function(data) {
                            console.log(data);
                            for (var i = 0; i < data.categories.length; i++) {
                              data.categories[i].category = data.categories[i].category.replace('<', '< $');
                              data.categories[i].category = data.categories[i].category.replace('>', '> $');
                            }
                            $scope.chartData = data.categories;
                        },
                        function(data) {
                            console.log(data);
                        }
                    );

                }
            });

            BillModel.getCostResourceMonths({
                    id: $cookies.getObject('awsKey')
                },
                function(data) {
                    if ('message' in data) {
                      $scope.awsCostResourceMonthsNoDataMessage = data['message'];
                    } else {
                      $scope.awsCostResourceMonthsNoDataMessage = null;
                      $scope.months = data.months;
                      $scope.selectedMonth = $scope.months[$scope.months.length - 1];
                    }
                },
                function(data) {
                    console.log(data);
                });

            $scope.getFormattedCatLabel = function(catLabel) {
                catLabel = catLabel.replace('<', '< $');
                catLabel = catLabel.replace('>', '> $');
                return catLabel;
            };

            $scope.getFormattedMonth = function(month) {
                if (month)
                    return month.replace('-01', '');
            }

            $scope.getLastCategory = function(cat) {
                if (cat) {
                    return Object.keys(cat).length - 1;
                }
                return 0;
            }

            $scope.chartOptions = {
                chart: {
                    type: 'pieChart',
                    height: 400,
                    x: function(d) {
                        return d.category;
                    },
                    y: function(d) {
                        return d.total;
                    },
                    showLabels: true,
                    showLegend: false,
                    valueFormat: function(n) {
                        return ('$' + n.toFixed(2));
                    },
                    duration: 1000,
                    legend: {
                        margin: {
                            top: 5,
                            right: 35,
                            bottom: 5,
                            left: 0
                        }
                    }
                }
            };


        }
    ])
    .controller('GCCostResourceCtrl', ['$scope', 'BillModel', '$cookies',
        function($scope, BillModel, $cookies) {

            $scope.getFormattedMonth = function(month) {
                if (month)
                    return month.replace('-01', '');
            }

            $scope.getFormattedCatLabel = function(catLabel) {
                catLabel = catLabel.replace('<', '< $');
                catLabel = catLabel.replace('>', '> $');
                return catLabel;
            };

            function parseMonthChart(month) {
                console.log(month);
                var res = [];

                for (var key in month.categories) {
                    if (month.categories.hasOwnProperty(key)) {
                        var tmp = {
                            resource: $scope.getFormattedCatLabel(key),
                            cost: month.categories[key]['total']
                        }
                        res.push(tmp);
                    }
                }
                console.log(res);
                return res;
            }

            $scope.$watch('selectedMonth', function(newValue) {
                if (newValue) {
                    for (var i = 0; i < newValue.categories.length; i++) {
                        newValue.categories[i].resources.sort(function(a, b) {
                            return (a.cost > b.cost) ? -1 : ((b.cost > a.cost) ? 1 : 0);
                        });
                    }
                    $scope.categories = newValue.categories;
                    $scope.selectedTab = 0;
                    $scope.chartData = parseMonthChart(newValue);

                    //Filling searchPool for search input
                    $scope.searchPool = [];
                    for (var key in newValue.categories) {
                        if (newValue.categories.hasOwnProperty(key)) {
                            $scope.searchPool = $scope.searchPool.concat(newValue.categories[key].resources);
                        }
                    }
                }
            });

            BillModel.getGCCostResource({
                id: $cookies.getObject('gcKey')
            }, function(data) {
                console.log(data);
                $scope.months = data.months;
                $scope.selectedMonth = $scope.months[$scope.months.length - 1];
                $scope.dataLoaded = true;

            }, function(data) {
                console.log(data);
            });


            $scope.chartOptions = {
                chart: {
                    type: 'pieChart',
                    height: 400,
                    x: function(d) {
                        return d.resource;
                    },
                    y: function(d) {
                        return d.cost;
                    },
                    showLabels: true,
                    showLegend: false,
                    valueFormat: function(n) {
                        return ('$' + n.toFixed(2));
                    },
                    duration: 1000,
                    legend: {
                        margin: {
                            top: 5,
                            right: 35,
                            bottom: 5,
                            left: 0
                        }
                    }
                }
            };

        }
    ]);
