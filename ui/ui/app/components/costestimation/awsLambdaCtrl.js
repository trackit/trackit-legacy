'use strict';

angular.module('trackit.statistics')

    .controller('AWSLambdaCtrl', ['$scope', 'EstimationModel', '$cookies', '$filter', '$timeout',
        function($scope, EstimationModel, $cookies, $filter, $timeout) {

            var orderBy = $filter('orderBy');
            var showLimit = 20;

            $scope.dataLoaded = false;
            $scope.predicate = null;
            $scope.reverse = null;
            $scope.show = showLimit;

            $scope.lambdaSearchChanged = function(search) {
                $scope.show = (search.length ? 1000 : showLimit);
            };

            EstimationModel.getLambda({
                    id: $cookies.getObject('awsKey')
                },
                function(data) {
                    if ('message' in data) {
                      $scope.awsLambdaNoDataMessage = data.message;
                    } else {
                      $scope.aws_lambda_resources = data['lambdas'];
                      $scope.has_free_tier = false;
                      $scope.aws_lambda_resources.forEach((lambda) => {
                          lambda.free_tier = (lambda.raw_cost && lambda.cost !== lambda.raw_cost)
                          $scope.has_free_tier = ($scope.has_free_tier || lambda.free_tier);
                      });
                      $scope.order('requests');
                      $scope.dataLoaded = true;
                    }
                    // Give time to ng-repeat to insert elements in the DOM
                    $timeout(function() {
                        $scope.itemsLength = angular.element('tbody > tr.resource-item').length;
                    }, 500);
                });

            $scope.order = function(predicate) {
                $scope.predicate = predicate;
                $scope.reverse = ($scope.predicate === predicate) ? !$scope.reverse : false;
                $scope.aws_lambda_resources = orderBy($scope.aws_lambda_resources, predicate, $scope.reverse);
            };

            $scope.showMore = function() {
                $scope.show += showLimit;
            };

            $scope.getDailyEstimation = (free_tier=false) => {
                var total = 0;
                for (var i=0; i < $scope.aws_lambda_resources.length; i++)
                    total += (free_tier ? $scope.aws_lambda_resources[i].raw_cost : $scope.aws_lambda_resources[i].cost);
                return total;
            };

            $scope.getMonthlyEstimation = (free_tier=false) => {
                return $scope.getDailyEstimation(free_tier) * 30;
            };
        }
    ]);
