'use strict';

angular.module('trackit')
  .controller('ConfirmationModalCtrl', ['$scope', '$uibModalInstance', 'modalParams',
    function($scope, $uibModalInstance, modalParams) {

      $scope.modalTitle = modalParams.modalTitle;
      $scope.modalText = modalParams.modalText;

      $scope.proceed = function() {
        $uibModalInstance.close('proceeded');
      };

      $scope.cancel = function() {
        $uibModalInstance.dismiss('cancel');
      };

    }
  ]);
