trackit.factory('SuggestionsModel', ['$resource', 'Config',
  function($resource, Config) {

    return $resource("/mock/", {}, {
      getUnderutilized: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/underutilized")
      },
      getOndemandSwitch: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/ondemandswitchsuggestion")
      },
      getAvailableVolumes: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/availablevolumes")
      },
      getStoppedInstances: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/stoppedinstances")
      }
    });
  }
]);
