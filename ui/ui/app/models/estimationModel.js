trackit.factory('EstimationModel', ['$resource', 'Config',
  function($resource, Config) {
    return $resource("/mock/", {}, {
      getAWSVMs: {
        method: "GET",
        url: Config.apiUrl("/compare_providers/aws/:id")
      },
      getGCVMs: {
        method: "GET",
        url: Config.apiUrl("/compare_providers/gcloud/:id")
      },
      getRDSEstimation: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/rds/cost_estimation")
      },
      getS3Estimation: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/s3/space_usage")
      },
      getS3SpaceUsageTree: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/s3/space_usage_directory")
      },
      getS3SpaceUsageTags: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/s3/space_usage_tags")
      },
      getPrediction: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/reservationforecast")
      },
      getELB: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/describe_elb")
      },
      getLambda: {
          method: "GET",
          url: Config.apiUrl("/aws/accounts/:id/lambda/usage")
      },
      getCSVExport: {
          method: "GET",
          url: Config.apiUrl("/aws/accounts/:id/csv/export")
      },
      getCSV: {
          method: "GET",
          url: Config.apiUrl("/aws/accounts/:id/stats/:end?csv")
      }
    });
  }
]);
