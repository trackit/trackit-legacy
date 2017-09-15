trackit.factory('BillModel', ['$resource', 'Config',
  function($resource, Config) {
    return $resource("/aws/account/:id/", {}, {
      // Cost by product (pie chart on home)
      getBillPie: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/monthlycostbyproduct/1?show=6")
      },
      getGCBillPie: {
        method: "GET",
        url: Config.apiUrl("/gcloud/identity/:id/stats/monthcostbyproduct")
      },
      // Cost by project
      getGCCostProject: {
        method: "GET",
        url: Config.apiUrl("/gcloud/identity/:id/stats/costbyproject")
      },
      // Cost by usage
      getCUCostUsage: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/usagecost")
      },
      getGCCostUsage: {
        method: "GET",
        url: Config.apiUrl("/gcloud/identity/:id/stats/usagecost")
      },
      getGCCostResource: {
        method: "GET",
        url: Config.apiUrl("/gcloud/identity/:id/stats/costbyresource")
      },
      // Cost by resource months
      getCostResourceMonths: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/costbyresource/months")
      },
      // Cost by resource
      getCostResourceCategories: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/costbyresource/:month/categories")
      },
      getCostResourceCategory: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/costbyresource/:month/:category")
      },
      getCostResourceSearch: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/costbyresource/:month/search/:search")
      },
      getCostResourceChart: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/costbyresource/:month/chart")
      },
      getS3MostUsed: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/s3/most_accessed_objects")
      },
      getS3LastAccessed: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/s3/last_accessed_bucket")
      },
      getTags: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/tags")
      },
      getTagsOnlyWithData: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/tags_only_with_data")
      },
      getTagDetails: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/costbytag/:tag")
      },
      getCPUTagHourly: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/cpuhourlyusagebytag/:tag")
      },
      getCPUTagDaily: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/cpudaysweekusagebytag/:tag")
      },
      //CPU usage per week
      getCpuUsageDay: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/cpudaysweekusage")
      },
      //CPU usage per hour
      getCpuUsageHour: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/stats/cpuhourlyusage")
      },
      getEC2BandwidthCost: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/ec2_bandwidth_costs")
      },
      getS3BandwidthCost: {
        method: "GET",
        url: Config.apiUrl("/aws/accounts/:id/s3_bandwidth_costs")
      },
    });
  }
]);
