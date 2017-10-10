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
	        $scope.AWSStatsLoaded = false;

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

	            EstimationModel.getEC2({
		            id: $scope.awsKey
	            }, (data) => {
		            let stat = data.stats[0];
	            $scope.AWSstats = {
		            total: stat.reserved + stat.stopped + stat.unreserved,
		            reservations: stat.unused + stat.reserved,
		            onDemand: stat.unreserved,
		            reserved: stat.reserved,
		            stopped: stat.stopped
	            };
	            $scope.reserved_report = stat.reserved_report;
	            $scope.AWSStatsLoaded = true;
            }, (data) => {
		            $scope.AWSstats = {
			            total: 'N/A',
			            reservations: 'N/A',
			            onDemand: 'N/A',
			            reserved: 'N/A',
			            stopped: 'N/A'
		            };
		            $scope.AWSStatsLoaded = false;
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

            // Providers information

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

            // AWS Instances

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
                        setTimeout(() => {
                            window.dispatchEvent(new Event('resize'));
                        }, 1000);
                    }
                }, function (data) {
                    console.log(data);
                });

                $scope.s3DataLoaded = false;
                $scope.s3Buckets = [];
                $scope.s3Transfers = [];
                $scope.s3TransfersChart = [];
                $scope.s3Tags = ["All tags"];
                $scope.s3TagSelected = $scope.s3Tags[0];

                let getS3Buckets = () => {
                    let setData = (data) => {
                        $scope.s3Buckets = data.accounts;
                        $scope.s3Transfers = getS3TransfersList();
                        setTimeout(() => {
                            $scope.s3TransfersChart = getS3TransfersChart();
                            $scope.s3DataLoaded = true;
                        }, 300);
                    };

                    if ($scope.s3TagSelected !== $scope.s3Tags[0])
                        EstimationModel.getS3BucketsPerTag({
                            id: $scope.awsKey,
                            tag: $scope.s3TagSelected
                        }, setData);
                    else
                        EstimationModel.getS3BucketsPerName({
                            id: $scope.awsKey
                        }, setData);
                };

                EstimationModel.getS3Tags({
                    id: $scope.awsKey
                }, (data) => {
                    $scope.s3Tags = $scope.s3Tags.concat(data.tags);
                    getS3Buckets();
                });

                $scope.selectTag = (tag) => {
                    $scope.s3TagSelected = tag;
                    getS3Buckets();
                };
            }

            // GCP Instances

            if ($scope.gcSelectedKey) {
                /* Get GCP Storage */
            }

            // Filters / Pagination

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

            // Global instances list

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

            // S3 Buckets list

            let getS3TransfersList = () => {
                let transfers = [];
                $scope.s3Buckets.forEach((bucket) => {
                    Object.keys(bucket).forEach((key) => {
                        if (key.endsWith("-Bytes") && transfers.indexOf(key) === -1)
                            transfers.push(key);
                    });
                });
                transfers.sort();
                return transfers;
            };

            $scope.getS3Buckets = () => {
                return $scope.s3Buckets;
            };

            $scope.getFilteredS3Buckets = () => {
                let buckets = $scope.getS3Buckets();
                if (!$scope.searchPattern || !$scope.searchPattern.length)
                    return buckets;
                return $filter('regex')(buckets, $scope.searchPattern)
            };

            $scope.getOrderedS3Buckets = () => {
                let buckets = $scope.getFilteredS3Buckets();
                if (!$scope.predicate || !$scope.predicate.length)
                    return buckets;
                return $filter('orderBy')(buckets, $scope.predicate, $scope.reverse);
            };

            $scope.getPaginatedS3Buckets = () => {
                let buckets = $scope.getOrderedS3Buckets();
                let first = ($scope.pagination.current - 1) * $scope.pagination.size;
                let last = first + $scope.pagination.size;
                return buckets.slice(first, last);
            };

            // S3 Buckets charts

            $scope.s3ChartsOptions = {
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
                        axisLabel: 'Transfer'
                    },
                    yAxis: {
                        axisLabel: 'Size',
                        axisLabelDistance: 20,
                        tickFormat: function(d) {
                            return $filter("bytes")(d);
                        }
                    }
                }
            };

            let getS3TransfersChart = () => {
                return $scope.s3Buckets.map((bucket) => {
                    let values = $scope.s3Transfers.map((key) => {
                        return {x: key, y: (key in bucket ? bucket[key] : 0)};
                    });
                    return {key: bucket.name, values};
                });
            };

            // Misc

            $scope.getProgressType = (percent)  => {
                if (percent < 30)
                    return "success";
                else if (percent >= 30 && percent < 70)
                    return "warning";
                else if (percent >= 70)
                    return "danger";
            };

        }])
    .filter('truncate', function () {
        return function (value) {
            return Math.trunc(value);
        };
    });
