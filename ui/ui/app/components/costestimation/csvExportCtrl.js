'use strict';

angular.module('trackit.statistics')

    .controller('CSVExportCtrl', ['$scope', 'Config', 'EstimationModel', '$cookies', '$filter', '$timeout',
        function($scope, Config, EstimationModel, $cookies, $filter, $timeout) {

            var showLimit = 20;

            $scope.dataLoaded = false;
            $scope.predicate = null;
            $scope.show = showLimit;

            EstimationModel.getCSVExport({
                    id: $cookies.getObject('awsKey')
                },
                function(data) {
                    if ('message' in data) {
                      $scope.awsCSVNoDataMessage = data.message;
                    } else {
                      $scope.csv_export = data['csvs'];
                      $scope.dataLoaded = true;
                    }
                    // Give time to ng-repeat to insert elements in the DOM
                    $timeout(function() {
                        $scope.itemsLength = angular.element('tbody > tr.resource-item').length;
                    }, 500);
                });

            $scope.showMore = function() {
                $scope.show += showLimit;
            };

            $scope.download = function download(end) {
                EstimationModel.getCSV({
                        id: $cookies.getObject('awsKey'),
                        end: end
                    },
                    function(data) {
                        var processed_data = '';
                        for(var p in data){
                            if(typeof data[p] == 'string'){
                                processed_data += data[p];
                            }
                        }
                        document.location = 'data:text/csv;charset=utf-8,' +
                            encodeURIComponent(processed_data);
                    });
            }
        }
    ]);
