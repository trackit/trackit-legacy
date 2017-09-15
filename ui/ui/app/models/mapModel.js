trackit.factory('MapModel', ['$resource', 'apiBaseUrl',
    function($resource, apiBaseUrl) {


        return $resource(apiBaseUrl + '/aws/', {}, {
          getS3Pricing: {
              method: "GET",
              url: apiBaseUrl + "/aws/s3pricing?gigabytes=:size"
          },
          getGCPricing: {
              method: "GET",
              url: apiBaseUrl + "/gcloud/map?gigabytes=:size"
          },
          getAzurePricing: {
              method: "GET",
              url: apiBaseUrl + "/azure/storage/map?gigabytes=:size"
          },
            getS3Estimation: {
                method: "GET",
                url: apiBaseUrl + "/aws/accounts/:id/s3/space_usage"
            }
        });
    }
]);
