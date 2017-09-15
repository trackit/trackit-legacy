trackit.factory('StorageEstimateModel', ['$resource', 'Config',
    function($resource, Config) {


        return $resource(Config.apiUrl('/aws'), {}, {
          getAWSPricing: {
              method: "GET",
              url: Config.apiUrl("/aws/s3/estimate")
          },
          getAzurePricing: {
              method: "GET",
              url: Config.apiUrl("/azure/storage/estimate")
          }
        });
    }
]);
