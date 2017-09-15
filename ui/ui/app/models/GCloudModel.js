trackit.factory('GCloudModel', ['$resource', 'Config',
    function($resource, Config) {
        return $resource(Config.apiUrl('/aws'), {}, {
          getIdentities: {
              method: "GET",
              url: Config.apiUrl("/gcloud/identity")
          },
          remove: {
              method: "DELETE",
              url: Config.apiUrl("/gcloud/identity/:id")
          }
        });
    }
]);
