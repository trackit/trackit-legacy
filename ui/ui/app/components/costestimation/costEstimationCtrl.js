'use strict';

angular.module('trackit.prediction')
    .controller('CostEstimationCtrl', ['$scope', 'EstimationModel', '$cookies', '$filter', '$timeout', '$sce', '$uibModal', '$stateParams',
        function($scope, EstimationModel, $cookies, $filter, $timeout, $sce, $uibModal, $stateParams) {

            // Optional provider on storage
            if ($stateParams.optprov) {
                $scope.optionalProvider = $stateParams.optprov;
            }



            console.log($stateParams);


            $scope.getCostForOptionalProvider = function(byteSize) {
                var baseCost = 0.016;
                var gigSize = byteSize / (Math.pow(1024, 3));
                return (gigSize * baseCost);
            }

            $scope.selectionOptionalPrice = function() {
                var res = 0;

                for (var i = 0; i < $scope.selection.length; i++) {
                    if ($scope.selection[i].selectype == 'storage') {
                        res += $scope.getCostForOptionalProvider($scope.selection[i].used_space);
                    }
                }
                return res;
            };

            var awsSelectedKey = $cookies.getObject('awsKey');
            var gcSelectedKey = $cookies.getObject('gcKey');
            $scope.awsSelectedKey = awsSelectedKey;
            $scope.gcSelectedKey = gcSelectedKey;
            $scope.tabActive = 0;

            $scope.deselectedTab = function(tabIndex) {
                // Emit event so children can empty spacy data when needed
                $scope.$broadcast('tabDeselected', tabIndex);
            }

            $scope.selectedTab = function(tabIndex) {
                console.log('Setting tab to ' + tabIndex);
                $scope.tabActive = tabIndex;
                $scope.$broadcast('tabSelected', tabIndex);
            }

            // TODO not updating uib-tabset for some reason
            if ($stateParams.selectedtab) {
                $scope.selectedTab($stateParams.selectedtab);
            }

            var orderBy = $filter('orderBy');

            $scope.show = 12;
            $scope.selection = [];
            $scope.estimations = [];

            $scope.searchHelp = $sce.trustAsHtml('<strong>Search through your instances</strong><br>You can use basic regex. Here are a few examples :<ul><li>es.*prod</li><li>vpn.*com$</li></ul> ');

            $scope.$watch('tabActive', function(newValue) {
                console.log(newValue);
                //$scope.$apply();
            });

            $scope.showMore = function() {
                $scope.show += 12;
            };

            $scope.getFormattedDate = function(timestamp) {
                var tmp = new Date(timestamp);
                return tmp.toLocaleString();
                //return (tmp.toDateString() +' '+tmp.toTimeString());
            }

            $scope.$watch('resourceSearch', function() {
                $timeout(function() {
                    $scope.itemsLength = angular.element('tbody > tr.resource-item').length;
                }, 300);
            });

            // SELECTION UTILITIES

            $scope.trimSelection = function(selection, type) {
                var res = [];

                for (var i = 0; i < selection.length; i++) {
                    if (selection[i].selectype == type)
                        res.push(selection[i]);
                }
                return res;
            };

            $scope.isTypeInSelection = function(type) {
                for (var i = 0; i < $scope.selection.length; i++) {
                    if ($scope.selection[i].selectype == type)
                        return true;
                }
                return false;
            }

            $scope.addToSelection = function(item, type) {
                item.selectype = type;
                if ($scope.selection.indexOf(item) == -1)
                    $scope.selection.push(item);
            };

            $scope.removeFromSelection = function(item) {
                var index = $scope.selection.indexOf(item);
                if (index > -1) {
                    $scope.selection.splice(index, 1);
                }
            };

            $scope.selectAll = function(results, type) {
                if (results) {
                    for (var i = 0; i < results.length; i++) {
                        if (!$scope.isInSelection(results[i]))
                            $scope.addToSelection(results[i], type);
                    }
                }
            };

            $scope.clearSelection = function() {
                $scope.selection = [];
            };

            $scope.isInSelection = function(item) {
                return $scope.selection.indexOf(item) == -1 ? false : true;
            };

            function orderWithProviderFirst(estimations, predicate) {
                var isProvider = [];
                var isNotProvider = [];

                for (var i = 0; i < estimations.length; i++) {
                    if (estimations[i].provider == predicate)
                        isProvider.push(estimations[i]);
                    else {
                        isNotProvider.push(estimations[i]);
                    }
                }

                isProvider = orderBy(isProvider, function(item) {
                    return getCostForProvider(predicate, item.prices);
                }, $scope.reverse);
                isNotProvider = orderBy(isNotProvider, function(item) {
                    return getCostForProvider(predicate, item.prices);
                }, $scope.reverse);

                return isProvider.concat(isNotProvider);

            }

            $scope.order = function(predicate) {
                $scope.predicate = predicate;
                $scope.reverse = ($scope.predicate === predicate) ? !$scope.reverse : false;
                if (predicate == 'aws' ||  predicate == 'gcloud' || predicate == 'azure') {
                    $scope.estimations = orderWithProviderFirst($scope.estimations, predicate);
                } else
                    $scope.estimations = orderBy($scope.estimations, predicate, $scope.reverse);
            };

            $scope.orderELB = function(predicate) {
                $scope.predicateELB = predicate;
                $scope.reverseELB = ($scope.predicateELB === predicate) ? !$scope.reverseELB : false;
                $scope.elbs = orderBy($scope.elbs, predicate, $scope.reverseELB);
            };

            $scope.orderStorage = function(predicate) {
                $scope.predicateStorage = predicate;
                $scope.reverseStorage = ($scope.predicateStorage === predicate) ? !$scope.reverseStorage : false;
                if (predicate == 'aws') {
                    $scope.storage = orderBy($scope.storage, function(item) {
                        return getCostForProvider('aws', item.prices);
                    }, $scope.reverseStorage);
                } else if (predicate == 'gcloud') {
                    $scope.storage = orderBy($scope.storage, function(item) {
                        return getCostForProvider('gcloud', item.prices);
                    }, $scope.reverseStorage);
                } else if (predicate == 'azure') {
                    $scope.storage = orderBy($scope.storage, function(item) {
                        return getCostForProvider('azure', item.prices);
                    }, $scope.reverseStorage);
                } else
                    $scope.storage = orderBy($scope.storage, predicate, $scope.reverseStorage);
            };

            $scope.orderDB = function(predicate) {
                $scope.predicateDB = predicate;
                $scope.reverseDB = ($scope.predicateDB === predicate) ? !$scope.reverseDB : false;
                if (predicate == 'mysql') {
                    $scope.dbs = orderBy($scope.dbs, function(item) {
                        return getCostForProvider('mysql', item.prices);
                    }, $scope.reverseDB);
                } else if (predicate == 'aurora') {
                    $scope.dbs = orderBy($scope.dbs, function(item) {
                        return getCostForProvider('aurora', item.prices);
                    }, $scope.reverseDB);
                } else if (predicate == 'postgres') {
                    $scope.dbs = orderBy($scope.dbs, function(item) {
                        return getCostForProvider('postgres', item.prices);
                    }, $scope.reverseDB);
                } else if (predicate == 'oracle') {
                    $scope.dbs = orderBy($scope.dbs, function(item) {
                        return getCostForProvider('oracle', item.prices);
                    }, $scope.reverseDB);
                } else if (predicate == 'sqlserver') {
                    $scope.dbs = orderBy($scope.dbs, function(item) {
                        return getCostForProvider('sqlserver', item.prices);
                    }, $scope.reverseDB);
                } else
                    $scope.dbs = orderBy($scope.dbs, predicate, $scope.reverseDB);
            };

            $scope.showStorageTreeModal = function(sto) {
                var modalInstance = $uibModal.open({
                    templateUrl: 'components/costestimation/storageTree.html',
                    controller: 'StorageTreeController',
                    scope: $scope.$new(true),
                    windowClass: 'storage-tree-modal',
                    resolve: {
                        selectedPath: function() {
                            return sto.name;
                        }
                    }
                });
            };

            function getSelectionTotal() {
                var res = 0;

                for (var i = 0; i < $scope.selection.length; i++) {
                    var temp = $scope.selection[i];
                    if (temp.selectype == 'vm')
                        res += $scope.getMonthEstimation(getCostForProvider(temp.provider, temp.prices));
                    else if (temp.selectype == 'storage')
                        res += getCostForProvider(temp.provider, temp.prices);
                }
                return res;
            }

            function getCostForProvider(provider, arr) {
                if (arr) {
                    for (var i = 0; i < arr.length; i++) {
                        if (arr[i].name == provider || arr[i].provider == provider ||
                            arr[i].name == 'mysql' && provider == 'mariadb' ||
                            arr[i].name == 'mariadb' && provider == 'mysql')
                            return arr[i].cost;
                    }
                }
                return 0.0;
            }

            function getTotalForProvider(provider, arr) {
                var res = 0;

                for (var i = 0; i < arr.length; i++) {
                  if (arr[i].provider === provider) {
                    res += getCostForProvider(provider, arr[i].prices)
                  }
                }
                return res;
            }

            function getTotalForEngine(engine, arr) {
                var res = 0;



                for (var i = 0; i < arr.length; i++) {
                    if (arr[i].engine == engine || (arr[i].engine == 'mariadb' && engine == 'mysql')) {

                        res += getCostForProvider(engine, arr[i].prices)

                    }
                }
                return res;
            }

            function getEstimationFullProvider(provider, arr) {
                var res = 0;

                for (var i = 0; i < arr.length; i++) {
                    res += getCostForProvider(provider, arr[i].prices)
                }
                return res;
            }

            function getProgressType(percent) {
                if (percent < 30)
                    return "success";
                else if (percent >= 30 && percent < 70)
                    return "warning";
                else if (percent >= 70)
                    return "danger";
            }

            function isCPUDowngradable(item) {
                if (item.cpu_usage < 2 && item.bandwidth_usage < 30 && item.io_usage < 30)
                    return true;
                return false;
            }

            function isIODowngradable(item) {
                if (item.io_usage < 2 && item.bandwidth_usage < 30 && item.cpu_usage < 30)
                    return true;
                return false;
            }

            function isBandwidthDowngradable(item) {
                if (item.bandwidth_usage < 2 && item.io_usage < 30 && item.cpu_usage < 30)
                    return true;
                return false;
            }

            function isCPUUpgradable(item) {
                if (item.cpu_usage > 75 && (item.bandwidth_usage > 5 || item.io_usage > 5))
                    return true;
                return false;
            }

            function isIOUpgradable(item) {
                if (item.io_usage > 75 && (item.bandwidth_usage > 5 || item.cpu_usage > 5))
                    return true;
                return false;
            }

            function isBandwidthUpgradable(item) {
                if (item.bandwidth_usage > 75 && (item.io_usage > 5 || item.cpu_usage > 5))
                    return true;
                return false;
            }


            function getDowngradable(arr) {
                var exclude = ['m3.medium', 'c3.large', 'r3.large', 't2.nano', 'g2.2xlarge', 'i2.xlarge', 'd2.xlarge'];
                var res = [];

                for (var i = 0; i < arr.length; i++) {
                    var toggle = false;
                    var tmp = arr[i];
                    tmp.reasons = [];


                    if (exclude.indexOf(tmp.size) == -1) {
                        if (isCPUDowngradable(tmp)) {
                            tmp.reasons.push("CPU Usage is very low : " + tmp.cpu_usage.toFixed(2) + "%");
                            toggle = true;
                        }
                        if (isBandwidthDowngradable(tmp)) {
                            tmp.reasons.push("Bandwidth Usage is very low : " + tmp.bandwidth_usage.toFixed(2) + "%");
                            toggle = true;
                        }
                        if (isIODowngradable(tmp)) {
                            tmp.reasons.push("I/O Usage is very low : " + tmp.io_usage.toFixed(2) + "%");
                            toggle = true;
                        }

                        if (toggle) {
                            res.push(tmp);
                        }
                    }
                }
                return res;
            }

            function getUpgradable(arr) {
                var upres = [];

                for (var i = 0; i < arr.length; i++) {

                    var toggle = false;
                    var upTmp = arr[i];
                    upTmp.upReasons = [];


                    if (isCPUUpgradable(upTmp)) {
                        upTmp.upReasons.push("CPU Usage is quite high : " + upTmp.cpu_usage.toFixed(2) + "%");
                        toggle = true;
                    }
                    if (isBandwidthUpgradable(upTmp)) {
                        upTmp.upReasons.push("Bandwidth Usage is quite high : " + upTmp.bandwidth_usage.toFixed(2) + "%");
                        toggle = true;
                    }
                    if (isIOUpgradable(upTmp)) {
                        upTmp.upReasons.push("I/O Usage is quite high : " + upTmp.io_usage.toFixed(2) + "%");
                        toggle = true;
                    }

                    if (toggle)
                        upres.push(upTmp);

                }
                return upres;

            }

            $scope.getProgressType = getProgressType;
            $scope.getCostForProvider = getCostForProvider;
            $scope.getTotalForProvider = getTotalForProvider;
            $scope.getSelectionTotal = getSelectionTotal;
            $scope.getEstimationFullProvider = getEstimationFullProvider;
            $scope.getMonthEstimation = function(total) {
                return total * 720;
            };
            $scope.getMonthEstimationFromDailyPrice = function(total) {
                return total * 30;
            };

            $scope.suggestionsOrder = function(predicate) {
                $scope.currentModal.order.predicate = predicate;
                $scope.currentModal.order.reverse = ($scope.currentModal.order.predicate === predicate) ? !$scope.currentModal.order.reverse : false;
            };

            $scope.openSuggestions = function(type) {
                $scope.currentModal = {
                    title: null,
                    data: null,
                    showDowngradable: false,
                    showUpgradable: false,
                    filter: null,
                    pagination: {
                        size: 10,
                        current: 1,
                        indicators: 5
                    },
                    order: {
                        predicate: null,
                        reverse: false,
                        update: (predicate) => {
                            $scope.currentModal.order.predicate = predicate;
                            $scope.currentModal.order.reverse = ($scope.currentModal.order.predicate === predicate) ? !$scope.currentModal.order.reverse : false;
                        }
                    },
                    filteredData: () => {
                        if (!$scope.currentModal.filter || !$scope.currentModal.filter.length)
                            return $scope.currentModal.data;
                        return $filter('regex')($scope.currentModal.data, $scope.currentModal.filter)
                    },
                    orderedData: () => {
                        var filtered = $scope.currentModal.filteredData();
                        if ($scope.currentModal.order.predicate === 'aws' ||  $scope.currentModal.order.predicate === 'gcloud' || $scope.currentModal.order.predicate === 'azure')
                            return orderWithProviderFirst(filtered, $scope.currentModal.order.predicate);
                        else
                            return orderBy(filtered, $scope.currentModal.order.predicate, $scope.currentModal.order.reverse);
                    },
                    paginatedData: () => {
                        var ordered = $scope.currentModal.orderedData();
                        var first = ($scope.currentModal.pagination.current - 1) * $scope.currentModal.pagination.size;
                        var last = first + $scope.currentModal.pagination.size;
                        return ordered.slice(first, last);
                    }
                };
                if (type === 'downgradable') {
                    $scope.currentModal.title = 'Downgradable instances';
                    $scope.currentModal.data = $scope.downgradable;
                    $scope.currentModal.showDowngradable = true;
                } else if (type === 'upgradable') {
                    $scope.currentModal.title = 'Upgradable instances';
                    $scope.currentModal.data = $scope.upgradable;
                    $scope.currentModal.showUpgradable = true;
                }
                $uibModal.open({
                    animation:  true,
                    ariaLabelledBy: 'modal-title',
                    ariaDescribedBy: 'modal-body',
                    templateUrl: 'components/costestimation/suggestionsModal.html',
                    size: 'lg',
                    scope: $scope
                });
            };

            /* ACTIVE AWS KEY */
            if (awsSelectedKey) {
                /* AWS Vms */
                EstimationModel.getAWSVMs({
                    id: $cookies.getObject('awsKey')
                }, function(data) {
                    if ('message' in data) {
                      $scope.awsVMsNoDataMessage = data['message'];
                      $scope.dataLoaded = false;
                    } else {
                      $scope.awsVMsNoDataMessage = null;
                      if (data.result.length) {
                          $scope.vmsLastUpdated = data.last_updated;
                          $scope.vmsNextUpdate = data.next_update;
                          $scope.estimations = $scope.estimations.concat(data.result);
                          $scope.awsTotal = getTotalForProvider('aws', $scope.estimations);
                          $scope.gcloudTotal = getTotalForProvider('gcloud', $scope.estimations);
                          $scope.azureTotal = getTotalForProvider('azure', $scope.estimations);
                          $scope.grandTotal = $scope.awsTotal + $scope.gcloudTotal + $scope.azureTotal;
                          $scope.estimationFullAWS = getEstimationFullProvider('aws', $scope.estimations);
                          $scope.estimationFullGCloud = getEstimationFullProvider('gcloud', $scope.estimations);
                          $scope.estimationFullAzure = getEstimationFullProvider('azure', $scope.estimations);
                          $scope.downgradable = getDowngradable($scope.estimations);
                          $scope.upgradable = getUpgradable($scope.estimations);
                          $scope.dataLoaded = true;

                      }
                      // Give time to ng-repeat to insert elements in the DOM
                      $timeout(function() {
                          $scope.itemsLength = angular.element('tbody > tr.resource-item').length;
                      }, 500);
                    }
                }, function(data) {
                    console.log(data);
                });


                /* AWS DBs*/
                EstimationModel.getRDSEstimation({
                    id: $cookies.getObject('awsKey')
                }, function(data) {
                    if ('message' in data) {
                      $scope.awsDBsNoDataMessage = data['message'];
                      $scope.dataLoaded = false;
                    } else {
                      $scope.awsDBsNoDataMessage = null;
                      $scope.dbs = data.result;
                      $scope.dbsLastUpdated = data.last_updated;
                      $scope.dbsNextUpdate = data.next_update;
                      $scope.mysqlTotal = getTotalForEngine('mysql', $scope.dbs);
                      $scope.auroraTotal = getTotalForEngine('aurora', $scope.dbs);
                      $scope.postgreTotal = getTotalForEngine('postgres', $scope.dbs);
                      $scope.oracleTotal = getTotalForEngine('oracle', $scope.dbs);
                      $scope.sqlserverTotal = getTotalForEngine('sqlserver', $scope.dbs);

                      $scope.dbGrandTotal = $scope.mysqlTotal + $scope.auroraTotal +
                                            $scope.postgreTotal + $scope.oracleTotal +
                                            $scope.sqlserverTotal;
                    }
                }, function(data) {
                    console.log(data);
                });

                /*AWS Storage */
                EstimationModel.getS3Estimation({
                    id: $cookies.getObject('awsKey')
                }, function(data) {
                    if ('message' in data) {
                      $scope.awsStorageNoDataMessage = data['message'];
                      $scope.storageLoaded = false;
                    } else {
                      $scope.awsStorageNoDataMessage = null;
                      $scope.storage = data.buckets;
                      $scope.storageAwsTotal = getTotalForProvider('aws', $scope.storage);
                      $scope.storageGcloudTotal = getTotalForProvider('gcloud', $scope.storage);
                      $scope.storageAzureTotal = getTotalForProvider('azure', $scope.storage);
                      $scope.storageGrandTotal = $scope.storageAwsTotal + $scope.storageGcloudTotal + $scope.storageAzureTotal;
                      $scope.storageFullAws = getEstimationFullProvider('aws', $scope.storage);
                      $scope.storageFullGCloud = getEstimationFullProvider('gcloud', $scope.storage);
                      $scope.storageFullAzure = getEstimationFullProvider('azure', $scope.storage);

                      // If an optional provider is set, getting full transfer estimation
                      if ($scope.optionalProvider) {
                          $scope.storageFullOptional = function() {
                              var res = 0;
                              for (var i = 0; i < $scope.storage.length; i++) {
                                  res += $scope.getCostForOptionalProvider($scope.storage[i].used_space);
                              }
                              return res;
                          };
                      }

                      $scope.storageFullBestValue = function() {
                          var values = [$scope.storageFullAws, $scope.storageFullGCloud, $scope.storageFullAzure];
                          if ($scope.optionalProvider)
                              values.push($scope.storageFullOptional());
                          return Math.min.apply(null, values);
                      };

                      $scope.storageLoaded = true;
                      // Give time to ng-repeat to insert elements in the DOM
                      $timeout(function() {
                          $scope.storageItemsLength = angular.element('tbody > tr.storage-item').length;
                      }, 500);
                    }
                }, function(data) {
                    console.log(data);
                });

                EstimationModel.getELB({
                    id: $cookies.getObject('awsKey')
                }, function(data) {
                    if (data.elbs) {
                      $scope.elbs = data.elbs;
                      var totalCost = 0
                      for (var i = 0; i < $scope.elbs.length; i++) {
                        totalCost += $scope.elbs[i].cost;
                      }
                      $scope.elbsTotalCost = totalCost;
                      $scope.elbDataLoaded = true;
                    }
                    else if (data.message) {
                      $scope.elbMissingDataMessage = data.message;
                      $scope.elbDataLoaded = false;
                    }
                }, function(data) {
                    console.log(data);
                });
            }
            /* END ACTIVE AWS */

            /* ACTIVE GCloud */
            if (gcSelectedKey) {
                /* GC Vms */
                EstimationModel.getGCVMs({
                    id: gcSelectedKey
                }, function(data) {
                    console.log(data);
                    if (data.result.length) {
                        $scope.estimations = $scope.estimations.concat(data.result);
                        $scope.awsTotal = getTotalForProvider('aws', $scope.estimations);
                        $scope.gcloudTotal = getTotalForProvider('gcloud', $scope.estimations);
                        $scope.azureTotal = getTotalForProvider('azure', $scope.estimations);
                        $scope.grandTotal = $scope.awsTotal + $scope.gcloudTotal + $scope.azureTotal;
                        $scope.estimationFullAWS = getEstimationFullProvider('aws', $scope.estimations);
                        $scope.estimationFullGCloud = getEstimationFullProvider('gcloud', $scope.estimations);
                        $scope.estimationFullAzure = getEstimationFullProvider('azure', $scope.estimations);
                        $scope.downgradable = getDowngradable($scope.estimations);
                        $scope.upgradable = getUpgradable($scope.estimations);
                        $scope.dataLoaded = true;
                    }


                    // Give time to ng-repeat to insert elements in the DOM
                    $timeout(function() {
                        $scope.itemsLength = angular.element('tbody > tr.resource-item').length;
                    }, 500);

                }, function(data) {
                    console.log(data);
                });
            }
        }
    ])

.filter('regex', function() {
        return function(input, regex) {
            var patt = new RegExp(regex);
            var out = [];
            if (input)
                for (var i = 0; i < input.length; i++) {
                    if (patt.test(input[i]['name']) || patt.test(input[i]['size']))
                        out.push(input[i]);
                }
            return out;
        };
    })
    .filter('bytes', function() {
        return function(bytes, precision) {
            if (bytes==0 || isNaN(parseFloat(bytes)) || !isFinite(bytes)) return '-';
            if (typeof precision === 'undefined') precision = 1;
            var units = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'],
                number = Math.floor(Math.log(bytes) / Math.log(1024));
            return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) + ' ' + units[number];
        }
    });
