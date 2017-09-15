'use strict';

var module = angular.module('trackit.keyselect', ['trackit.aws.services', 'trackit.config']);

module.controller('KeyselectCtrl', ['$scope', 'AWSKey', '$cookies', 'Config', '$http', 'GCloudModel', '$rootScope', '$state', '$stateParams', 'ConfirmationModalFactory', '$uibModal',
        function($scope, AWSKey, $cookies, Config, $http, GCloudModel, $rootScope, $state, $stateParams, ConfirmationModalFactory, $uibModal) {

            var keys_error_status = [{
                label: "bad_key",
                message: "The key you entered is incorrect"
            }, {
                label: "billing_report_error",
                message: "There is an error in your billing report setup"
            }, {
                label: "no_such_bucket",
                message: "The billing bucket you specified does not exist"
            }, {
                label: "processing_error",
                message: "We encountered an error while processing this key"
            }];


            $scope.getErrorMessage = function(label) {
                for (var i = 0; i < keys_error_status.length; i++) {
                    if (keys_error_status[i].label == label)
                        return keys_error_status[i].message;
                }
            }



            if ($stateParams.fromLogin) {
                var awsSelectedKey = $cookies.getObject('awsKey');
                var gcSelectedKey = $cookies.getObject('gcKey');
                if (awsSelectedKey || gcSelectedKey) {
                    $state.go('app.home');
                }
            } else {
                /* Remove any existing key cookies */
                $cookies.remove('awsKey');
                $cookies.remove('gcKey');
            }

            $scope.selectedAWS = [];
            $scope.selectedGC = {};

            /* Retrieve AWS keys */
            getAWSKeys();

            /* Retrieve GCloud Identities */
            getGCIdentities();


            $scope.addKey = addAWSKey;
            $scope.removeKey = removeAWSKey;
            $scope.removeGCIdentity = removeGCIdentity;
            $scope.changeKey = changeAWSKey;
            $scope.userToken = $cookies.getObject('userToken').token;
            $scope.gcloudInit = gcloudInit;

            /* Launch TrackIt with selected keys */
            $scope.launchTrackit = function() {

                /* AWS cookie setup */
                if ($scope.selectedAWS.length) {
                    var expires = new Date();
                    expires.setDate(expires.getDate() + 2);

                    var selectedAwsKeys = $scope.selectedAWS.map(function(key) {
                        return key.id;
                    });

                    $rootScope.awsKey = selectedAwsKeys;
                    $cookies.putObject('awsKey', selectedAwsKeys, {
                        expires: expires
                    });
                }

                /* Google Cloud cookie setup */
                if ($scope.selectedGC.id) {
                    var expires = new Date();
                    expires.setDate(expires.getDate() + 2);

                    $rootScope.gcKey = $scope.selectedGC.id;
                    $cookies.putObject('gcKey', $scope.selectedGC.id, {
                        expires: expires
                    });
                }

                /* Event to trigger menu provider state refresh */
                $rootScope.$broadcast('keysChanged');


                $state.go('app.home');

            }


            $scope.selectAWS = function(item) {
                if (!$scope.selectedAWS.includes(item)) {
                    $scope.selectedAWS.push(item);
                    return true;
                } else {
                    return false;
                }
            };

            $scope.unselectAWS = function(item) {
                var index = $scope.selectedAWS.indexOf(item);

                if (index >= 0) {
                    $scope.selectedAWS.splice(index, 1);
                    return true;
                } else {
                    return false;
                }
            }

            $scope.toggleAWS = function(item) {
                return $scope.selectAWS(item) || $scope.unselectAWS(item);
            }

            $scope.selectGC = function(item) {
                $scope.selectedGC = item;
            };

            $scope.openPolicy = function(account) {
                var modalInstance = $uibModal.open({
                    ariaLabelledBy: 'modal-title',
                    ariaDescribedBy: 'modal-body',
                    templateUrl: 'components/keyselect/policyModal.html',
                    controller: 'PolicyCtrl',
                    resolve: {
                        maccount: function() {
                            return account;
                        }
                    }
                });
            };

            /* Add an AWS key to the database for the user. */
            function addAWSKey(key) {
                AWSKey.add({
                    key: key.key,
                    secret: key.secret,
                    pretty: key.pretty || null,
                    billing_bucket_name: key.billing_bucket_name || null
                }, function() {
                    getAWSKeys();
                    $scope.showNewKeyForm = false;
                });
                key.key = '';
                key.secret = '';
                key.pretty = '';
                key.billing_bucket_name = '';
            }

            /* Remove an AWS key from the database for the user. */
            function removeAWSKey(key) {
                var confirmationModalInstance = new ConfirmationModalFactory('Delete AWS key', 'You are about to delete this AWS key. Proceed ?');
                confirmationModalInstance.result.then(function() {
                    AWSKey.remove({
                            id: key.id
                        },
                        function() {
                            getAWSKeys();
                        });
                }, function() {
                    console.log('Canceled');
                });
            }

            function removeGCIdentity(id) {
                var confirmationModalInstance = new ConfirmationModalFactory('Delete GCloud Identity', 'You are about to delete this identity. Proceed ?');
                confirmationModalInstance.result.then(function() {
                    GCloudModel.remove({
                        id: id
                    }, function(data) {
                        console.log(data);
                        getGCIdentities();
                    }, function(data) {
                        console.log(data);
                    });
                }, function() {
                    console.log('Canceled');
                });
            }

            /* Change an AWS key in-database for the user. */
            function changeAWSKey(key) {
                var params = {};
                if (key.key)
                    params.key = key.key;
                if (key.secret)
                    params.secret = key.secret;
                if (key.pretty)
                    params.pretty = key.pretty;
                if (key.billing_bucket_name)
                    params.billing_bucket_name = key.billing_bucket_name;
                AWSKey.change({
                        id: key.id
                    },
                    params,
                    function() {
                        getAWSKeys();
                        $scope.showChangeKeyForm = false;
                    });
            }

            function getAWSKeys(callback) {
                var tk = AWSKey.query({}, function() {
                    // Sorting the keys by their pretty name alphabetic values
                    tk.accounts = tk.accounts.sort(function(a, b) {
                        if (a.pretty.toUpperCase() < b.pretty.toUpperCase())
                            return -1;
                        else
                            return 1;
                    });
                    // Set $scope.keys only when the values have arrived
                    // to avoid displaying an empty list for an instant.
                    $scope.keys = tk;
                    if (!$scope.keys.accounts.length)
                        $scope.showNewKeyForm = true;
                    if (typeof(callback) === 'function')
                        callback();
                }, function() {
                    $scope.errorKey = true;
                });
            }

            function getGCIdentities() {
                GCloudModel.getIdentities(function(data) {
                    console.log(data);
                    $scope.identities = data.identities;
                }, function(data) {
                    console.log(data);
                });
            }

            function gcloudInit() {
                $http.get(Config.apiUrl('/gcloud/identity/initiate')).then(function(data) {
                    if (data) {
                        data = data.data;
                        window.location.assign(data.uri);
                    }
                });
            }
        }
    ])
    .controller('PolicyCtrl', ['$scope', '$uibModalInstance', 'maccount',
        function($scope, $uibModalInstance, maccount) {

            if (maccount.billing_bucket_name) {
                $scope.name = maccount.billing_bucket_name;
                $scope.dataLoaded = true;
            }

            $scope.close = function() {
                $uibModalInstance.close();
            };
        }
    ]);
