'use strict';

var module = angular.module('trackit.storage');

module.controller('StorageCtrl', function($scope, $timeout, StorageEstimate, StorageEstimateModel) {
    var pendingEstimate = null;


    // The list of units to be used in a selector
    $scope.units = [{
        name: 'B',
        size: 1
    }, {
        name: 'KB',
        size: Math.pow(10, 3)
    }, {
        name: 'KiB',
        size: Math.pow(2, 10)
    }, {
        name: 'MB',
        size: Math.pow(10, 6)
    }, {
        name: 'MiB',
        size: Math.pow(2, 20)
    }, {
        name: 'GB',
        size: Math.pow(10, 9)
    }, {
        name: 'GiB',
        size: Math.pow(2, 30)
    }, {
        name: 'TB',
        size: Math.pow(10, 12)
    }, {
        name: 'TiB',
        size: Math.pow(2, 40)
    }, {
        name: 'PB',
        size: Math.pow(10, 15)
    }, {
        name: 'PiB',
        size: Math.pow(2, 50)
    }, ]

    // Whether there is a request pending ( either started or delayed by the debouncer )
    $scope.pending = false;

    // Default values for the volumes
    $scope.volumes = {
        storage_standard: 0,
        storage_dra: 0,
        storage_nearline: 0,
        class_a_operations: 0,
        class_b_operations: 0,
        restore_nearline: 0,
        egress_americas_emea: 0,
        egress_asia_pacific: 0,
        egress_china: 0,
        egress_australia: 0,
        transfer_same_region: 0,
        transfer_same_multiregion: 0,
        transfer_region_multiregion: 0,
        transfer_multiregion_multiregion: 0,
    };

    // Units for the volumes
    $scope.defaultUnit = $scope.units[6]; // GiB
    $scope.volumeUnits = {
        storage_standard: $scope.defaultUnit,
        storage_dra: $scope.defaultUnit,
        storage_nearline: $scope.defaultUnit,
        class_a_operations: $scope.defaultUnit,
        class_b_operations: $scope.defaultUnit,
        restore_nearline: $scope.defaultUnit,
        egress_americas_emea: $scope.defaultUnit,
        egress_asia_pacific: $scope.defaultUnit,
        egress_china: $scope.defaultUnit,
        egress_australia: $scope.defaultUnit,
        transfer_same_region: $scope.defaultUnit,
        transfer_same_multiregion: $scope.defaultUnit,
        transfer_region_multiregion: $scope.defaultUnit,
        transfer_multiregion_multiregion: $scope.defaultUnit,
    };

    // Run the estimate on any change to the model

    // Adding delay so it doesn't fire a request for each user keystroke
    var timeoutPromise;
    var delayInMs = 1000;
    $scope.$watch(function() {
        var unitlessVolumes;

        unitlessVolumes = applyUnits($scope.volumes, $scope.volumeUnits);
        return unitlessVolumes;
    }, function() {
        $timeout.cancel(timeoutPromise); //does nothing, if timeout alrdy done

        timeoutPromise = $timeout(function() { //Set timeout

            $scope.runEstimate($scope.volumes, $scope.volumeUnits);

            StorageEstimateModel.getAWSPricing(applyUnits($scope.volumes, $scope.volumeUnits), function(data) {
                $scope.awsEstimate = data;
            }, function(data) {
                console.log(data);
            });

            StorageEstimateModel.getAzurePricing(applyUnits($scope.volumes, $scope.volumeUnits), function(data) {
                $scope.azureEstimate = data;
            }, function(data) {
                console.log(data);
            });

        }, delayInMs);

    }, true);





    // Run the estimate.
    //
    // The requests are debounced because :
    //   1. Angular attempts to perform the request several times
    //      when the page loads.
    //   2. We don't want to make a request for each keystroke from
    //      the user. Since it was done for reason 1. it would be
    //      pointless to also add input debouncing with ngModelOptions.
    $scope.runEstimate = function(volumes, units) {
        var timeout;
        var unitlessVolumes;

        // An estimate is now pending
        $scope.pending = true;

        // Cancel any previously pending estimate
        if (pendingEstimate) {
            pendingEstimate.cancel();
            pendingEstimate = null;
        }

        // Apply the units
        unitlessVolumes = applyUnits(volumes, units);

        // Set the debouncing timeout
        timeout = $timeout(function() {
            pendingEstimate = StorageEstimate(unitlessVolumes);
            pendingEstimate.promise.then(function(response) {
                $scope.pending = false;
                $scope.estimate = response.data;
                pendingEstimate = null;
            });
        }, 500); // 500ms debouncing.

        pendingEstimate = {
            timeout: timeout,
            cancel: function() {
                $timeout.cancel(timeout);
            }
        };
        return volumes;
    }

    // Apply a unit to a volume
    function applyUnit(volume, unit) {
        return volume * unit.size;
    }

    // Apply units to volumes
    function applyUnits(volumes, units) {
        var v;
        var result = {};

        for (v in volumes) {
            result[v] = applyUnit(volumes[v], units[v]);
        }
        return result;
    }
});

// All computations are made with millidollar as a unit. This filter prints it correctly.
module.filter('millidollars', ['currencyFilter', function(currencyFilter) {
    return function(input) {
        return currencyFilter(input / 1000);
    };
}]);
