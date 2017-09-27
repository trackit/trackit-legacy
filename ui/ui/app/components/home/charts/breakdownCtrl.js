'use strict';

angular.module('trackit.prediction')


.controller('BreakdownCtrl', ['$scope', '$http', 'Config', '$cookies',
  function($scope, $http, Config, $cookies) {

    // Key should be day or month or year (or any other key as long as it exists in data object)
    function transformProducts(data, timespec) {
        data = data[timespec + 's'];

        // Get products
        let products = [];
        data.forEach((item) => {
            item.products.forEach((product) => {
                if (products.indexOf(product.product) === -1)
                    products.push(product.product);
            });
        });

        // Generate columns for chart
        return products.map((key) => {
            // Get product value for each day/month/year/...
            let values = data.map(item => {
                // Default value of y is 0, in case of missing data for day/month/year/...
                let value = { x: item[timespec], y: 0 };
                item.products.forEach((product) => {
                    if (product.product === key)
                        value.y = product.cost;
                });
                return value;
            });
            return { key, values };
        });
    }

    $scope.dailyData3Days = null;
    $scope.dailyData30Days = null;
    $scope.monthlyData12Months = null;

    $http.get(Config.apiUrl("/aws/accounts/" + $cookies.getObject('awsKey') +  "/stats/dailycostbyproduct")).then(function(data) {
      if ('message' in data.data) {
        $scope.aws3DaysCostBreakdownNoDataMessage = data.data['message'];
      } else {
        $scope.aws3DaysCostBreakdownNoDataMessage = null;
        $scope.dailyData3Days = transformProducts(data.data, "day");
        // Bugfix to refresh NVD3 charts when data is loaded
        setTimeout(() => {
          window.dispatchEvent(new Event('resize'));
        }, 1000);
      }
    });

    $http.get(Config.apiUrl("/aws/accounts/" + $cookies.getObject('awsKey') +  "/stats/dailycostbyproduct/30")).then(function(data) {
      if ('message' in data.data) {
        $scope.aws30DaysCostBreakdownNoDataMessage = data.data['message'];
      } else {
        $scope.aws30DaysCostBreakdownNoDataMessage = null;
        $scope.dailyData30Days = transformProducts(data.data, "day");
        // Bugfix to refresh NVD3 charts when data is loaded
        setTimeout(() => {
          window.dispatchEvent(new Event('resize'));
        }, 1000);
      }
    });

    $http.get(Config.apiUrl("/aws/accounts/" + $cookies.getObject('awsKey') +  "/stats/monthlycostbyproduct/12")).then(function(data) {
      if ('message' in data.data) {
        $scope.aws12MonthsCostBreakdownNoDataMessage = data.data['message'];
      } else {
        $scope.aws12MonthsCostBreakdownNoDataMessage = null;
        $scope.monthlyData12Months = transformProducts(data.data, "month");
        // Bugfix to refresh NVD3 charts when data is loaded
        setTimeout(() => {
          window.dispatchEvent(new Event('resize'));
        }, 1000);
      }
    });

    function getMaxValue(data) {
      var res = 0;

      for (var i = 0; i < data.length; i++) {
        if (parseInt(data[i].y) > res)
          res = data[i].y;
      }
      return res;
    }

    $scope.optionsDailyChart = {
      chart: {
        type: 'multiBarChart',
        height: 400,
        margin: {
          top: 20,
          right: 20,
          bottom: 45,
          left: 85
        },
        showControls: true,
        clipEdge: false,
        duration: 500,
        stacked: true,
        xAxis: {
          axisLabel: 'Day',
          tickFormat: function(d) {
            var parts = d.split('-').map(function(v) { return parseInt(v, 10); });
            return d3.time.format('%x')(new Date(parts[0], parts[1] - 1, parts[2]))
          }
        },
        yAxis: {
          axisLabel: 'Cost',
          axisLabelDistance: 20,
          tickFormat: function(d) {
            return '$' + d3.format(',.2f')(d)
          }
        }
      }
    };

    $scope.optionsMonthlyChart = {
      chart: {
        type: 'multiBarChart',
        height: 400,
        margin: {
          top: 20,
          right: 20,
          bottom: 45,
          left: 85
        },
        showControls: true,
        clipEdge: false,
        duration: 500,
        stacked: true,
        xAxis: {
          axisLabel: 'Month',
          tickFormat: function(d) {
            var parts = d.split('-').map(function(v) { return parseInt(v, 10); });
            return d3.time.format('%m/%Y')(new Date(parts[0], parts[1] - 1, parts[2]))
          }
        },
        yAxis: {
          axisLabel: 'Cost',
          axisLabelDistance: 20,
          tickFormat: function(d) {
            return '$' + d3.format(',.2f')(d)
          }
        }
      }
    };

  }
])
.controller('GCBreakdownCtrl', ['$scope', '$http', 'Config', '$cookies',
  function($scope, $http, Config, $cookies) {

    function transformProducts(data, timespec) {
        data = data[timespec + 's'];

        // Get products
        let products = [];
        data.forEach((item) => {
            item.products.forEach((product) => {
                if (products.indexOf(product.product) === -1)
                    products.push(product.product);
            });
        });

        // Generate columns for chart
        return products.map((key) => {
            // Get product value for each day/month/year/...
            let values = data.map(item => {
                // Default value of y is 0, in case of missing data for day/month/year/...
                let value = {x: item[timespec], y: 0};
                item.products.forEach((product) => {
                    if (product.product === key)
                        value.y = product.cost;
                });
                return value;
            });
            return {key, values};
        });
    }

    $scope.data = null;

    $http.get(Config.apiUrl("/gcloud/identity/" + $cookies.getObject('gcKey') +  "/stats/dailycostbyproduct")).then(function(data) {
      $scope.data = transformProducts(data.data, "day");
    });

    $scope.data = null;

    $http.get(Config.apiUrl("/gcloud/identity/" + $cookies.getObject('gcKey') +  "/stats/dailycostbyproduct")).then(function(data) {
      $scope.data = transformProducts(data.data, "day");
    });

    function getMaxValue(data) {
      var res = 0;

      for (var i = 0; i < data.length; i++) {
        if (parseInt(data[i].y) > res)
          res = data[i].y;
      }
      return res;
    }



    $scope.options = {
      chart: {
        type: 'multiBarChart',
        height: 400,
        margin: {
          top: 20,
          right: 20,
          bottom: 45,
          left: 85
        },
        showControls: true,
        clipEdge: false,
        duration: 500,
        stacked: false,
        xAxis: {
          axisLabel: 'Day',
          tickFormat: function(d) {
            var parts = d.split('-').map(function(v) { return parseInt(v, 10); });
            return d3.time.format('%x')(new Date(parts[0], parts[1] - 1, parts[2]))
          }
        },
        yAxis: {
          axisLabel: 'Cost',
          axisLabelDistance: 20,
          tickFormat: (d) => ('$' + d3.format(',.2f')(d))
        }
      }
    };

  }
]);
