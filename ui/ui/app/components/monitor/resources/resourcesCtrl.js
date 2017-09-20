'use strict';

angular.module('trackit')
    .controller('ResourcesVMsCtrl', ['$scope', 'EstimationModel', 'AWSKey', '$cookies', '$filter', '$http', 'Config',
        function($scope, EstimationModel, AWSKey, $cookies, $filter, $http, Config) {

            $scope.awsSelectedKey = $cookies.getObject('awsKey');
            $scope.gcSelectedKey = $cookies.getObject('gcKey');

            $scope.providers = {
                aws: true,
                gcp: true,
                azure: true
            };

            $scope.selectedProviders = () => {
                let providers = [];
                Object.keys($scope.providers).map((provider) => {
                    if ($scope.providers[provider])
                        providers.push(provider);
                });
                return providers;
            };

            $scope.instances = {
                aws: [],
                gcp: [],
                azure: []
            };

            $scope.dataLoaded = false;

            if ($scope.awsSelectedKey) {
                EstimationModel.getAWSVMs({
                    id: $scope.awsSelectedKey
                }, function (data) {
                    $scope.awsDBsNoDataMessage = ('message' in data) ? data['message'] : null;
                    if (data.result.length) {
                        $scope.instances.aws = data.result;
                        $scope.dataLoaded = true;
                    }
                }, function (data) {
                    console.log(data);
                });
            }

            if ($scope.gcSelectedKey) {
                EstimationModel.getGCVMs({
                    id: $scope.gcSelectedKey
                }, function (data) {

                }, function (data) {
                    console.log(data);
                });
            }

            $scope.AWSStatsLoaded = false;

            $http.get(Config.apiUrl("/aws/accounts/" + $scope.awsSelectedKey + "/stats/instancestats")).then(function(res) {
                let stat = res.data.stats[0];
                if (stat) {
                    $scope.AWSstats = {
                        total: stat.reserved + stat.stopped + stat.unreserved,
                        reservations: stat.unused + stat.reserved,
                        onDemand: stat.unreserved,
                        reserved: stat.reserved,
                        stopped: stat.stopped
                    };
                    $scope.reserved_report = stat.reserved_report;
                    $scope.AWSStatsLoaded = true;
                } else {
                    $scope.AWSstats = {
                        total: 'N/A',
                        reservations: 'N/A',
                        onDemand: 'N/A',
                        reserved: 'N/A',
                        stopped: 'N/A'
                    };
                    $scope.AWSStatsLoaded = false;
                }
            });

            $scope.searchPattern = "";

            $scope.predicate = "";

            $scope.reverse = false;

            $scope.pagination = {
                size: 10,
                current: 1,
                indicators: 5
            };

            $scope.order = (predicate) => {
                $scope.reverse = ($scope.predicate === predicate) ? !$scope.reverse : false;
                $scope.predicate = predicate;
            };

            $scope.getInstances = () => {
                let instances = [];
                let providers = $scope.selectedProviders();
                providers.forEach((provider) => {
                    instances = instances.concat($scope.instances[provider]);
                });
                return instances;
            };

            $scope.getFilteredInstances = () => {
                let instances = $scope.getInstances();
                if (!$scope.searchPattern || !$scope.searchPattern.length)
                    return instances;
                return $filter('regex')(instances, $scope.searchPattern)
            };

            $scope.getOrderedInstances = () => {
                let instances = $scope.getFilteredInstances();
                if (!$scope.predicate || !$scope.predicate.length)
                    return instances;
                return $filter('orderBy')(instances, $scope.predicate, $scope.reverse);
            };

            $scope.getPaginatedInstances = () => {
                let instances = $scope.getOrderedInstances();
                let first = ($scope.pagination.current - 1) * $scope.pagination.size;
                let last = first + $scope.pagination.size;
                return instances.slice(first, last);
            };

            $scope.getProgressType = (percent)  => {
                if (percent < 30)
                    return "success";
                else if (percent >= 30 && percent < 70)
                    return "warning";
                else if (percent >= 70)
                    return "danger";
            };

        }])
    .controller('ResourcesDatabasesCtrl', ['$scope', 'EstimationModel', 'AWSKey', '$cookies', '$filter',
        function($scope, EstimationModel, AWSKey, $cookies, $filter) {

            $scope.awsSelectedKey = $cookies.getObject('awsKey');
            $scope.gcSelectedKey = $cookies.getObject('gcKey');

            $scope.providers = {
                aws: true,
                gcp: true,
                azure: true
            };

            $scope.selectedProviders = () => {
                let providers = [];
                Object.keys($scope.providers).map((provider) => {
                    if ($scope.providers[provider])
                        providers.push(provider);
                });
                return providers;
            };

            $scope.instances = {
                aws: [],
                gcp: [],
                azure: []
            };

            $scope.dataLoaded = false;

            if ($scope.awsSelectedKey) {
                EstimationModel.getRDSEstimation({
                    id: $scope.awsSelectedKey
                }, function (data) {
                    $scope.awsDBsNoDataMessage = ('message' in data) ? data['message'] : null;
                    if (data.result.length) {
                        $scope.instances.aws = data.result;
                        $scope.dataLoaded = true;
                    }
                }, function (data) {
                    console.log(data);
                });
            }

            if ($scope.gcSelectedKey) {
                /* Get GCP DBs */
            }

            $scope.searchPattern = "";

            $scope.predicate = "";

            $scope.reverse = false;

            $scope.pagination = {
                size: 10,
                current: 1,
                indicators: 5
            };

            $scope.order = (predicate) => {
                $scope.reverse = ($scope.predicate === predicate) ? !$scope.reverse : false;
                $scope.predicate = predicate;
            };

            $scope.getInstances = () => {
                let instances = [];
                let providers = $scope.selectedProviders();
                providers.forEach((provider) => {
                    instances = instances.concat($scope.instances[provider]);
                });
                return instances;
            };

            $scope.getFilteredInstances = () => {
                let instances = $scope.getInstances();
                if (!$scope.searchPattern || !$scope.searchPattern.length)
                    return instances;
                return $filter('regex')(instances, $scope.searchPattern)
            };

            $scope.getOrderedInstances = () => {
                let instances = $scope.getFilteredInstances();
                if (!$scope.predicate || !$scope.predicate.length)
                    return instances;
                return $filter('orderBy')(instances, $scope.predicate, $scope.reverse);
            };

            $scope.getPaginatedInstances = () => {
                let instances = $scope.getOrderedInstances();
                let first = ($scope.pagination.current - 1) * $scope.pagination.size;
                let last = first + $scope.pagination.size;
                return instances.slice(first, last);
            };

            $scope.getProgressType = (percent)  => {
                if (percent < 30)
                    return "success";
                else if (percent >= 30 && percent < 70)
                    return "warning";
                else if (percent >= 70)
                    return "danger";
            };

        }])
    .controller('ResourcesStoragesCtrl', ['$scope', 'EstimationModel', 'AWSKey', '$cookies', '$filter',
        function($scope, EstimationModel, AWSKey, $cookies, $filter) {

            $scope.awsSelectedKey = $cookies.getObject('awsKey');
            $scope.gcSelectedKey = $cookies.getObject('gcKey');

            $scope.providers = {
                aws: true,
                gcp: true,
                azure: true
            };

            $scope.selectedProviders = () => {
                let providers = [];
                Object.keys($scope.providers).map((provider) => {
                    if ($scope.providers[provider])
                        providers.push(provider);
                });
                return providers;
            };

            $scope.instances = {
                aws: [],
                gcp: [],
                azure: []
            };

            $scope.dataLoaded = false;

            if ($scope.awsSelectedKey) {
                EstimationModel.getS3Estimation({
                    id: $scope.awsSelectedKey
                }, function (data) {
                    $scope.awsDBsNoDataMessage = ('message' in data) ? data['message'] : null;
                    if (data.buckets.length) {
                        $scope.instances.aws = data.buckets;
                        $scope.dataLoaded = true;
                    }
                }, function (data) {
                    console.log(data);
                });
            }

            if ($scope.gcSelectedKey) {
                /* Get GCP Storage */
            }

            $scope.searchPattern = "";

            $scope.predicate = "";

            $scope.reverse = false;

            $scope.pagination = {
                size: 10,
                current: 1,
                indicators: 5
            };

            $scope.order = (predicate) => {
                $scope.reverse = ($scope.predicate === predicate) ? !$scope.reverse : false;
                $scope.predicate = predicate;
            };

            $scope.getInstances = () => {
                let instances = [];
                let providers = $scope.selectedProviders();
                providers.forEach((provider) => {
                    instances = instances.concat($scope.instances[provider]);
                });
                return instances;
            };

            $scope.getFilteredInstances = () => {
                let instances = $scope.getInstances();
                if (!$scope.searchPattern || !$scope.searchPattern.length)
                    return instances;
                return $filter('regex')(instances, $scope.searchPattern)
            };

            $scope.getOrderedInstances = () => {
                let instances = $scope.getFilteredInstances();
                if (!$scope.predicate || !$scope.predicate.length)
                    return instances;
                return $filter('orderBy')(instances, $scope.predicate, $scope.reverse);
            };

            $scope.getPaginatedInstances = () => {
                let instances = $scope.getOrderedInstances();
                let first = ($scope.pagination.current - 1) * $scope.pagination.size;
                let last = first + $scope.pagination.size;
                return instances.slice(first, last);
            };

            $scope.getProgressType = (percent)  => {
                if (percent < 30)
                    return "success";
                else if (percent >= 30 && percent < 70)
                    return "warning";
                else if (percent >= 70)
                    return "danger";
            };

        }]);
