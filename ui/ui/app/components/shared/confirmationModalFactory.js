'use strict';

trackit.factory('ConfirmationModalFactory', function($uibModal) {
  return function(modalTitle, modalText) {

    var modalInstance = $uibModal.open({
      templateUrl: '/components/shared/confirmationModal.html',
      controller: 'ConfirmationModalCtrl',
      resolve: {
        modalParams : function() {
          return {
            'modalTitle' : modalTitle,
            'modalText' : modalText
          };
        }
      }
    });

    return modalInstance;
  };
});
