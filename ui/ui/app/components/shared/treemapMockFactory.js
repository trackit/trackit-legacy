'use strict';

trackit.factory('TreemapMockFactory', function() {
    return function() {

        var now = Date.now();

        function subDays(toSub, days) {
          return toSub - ((1000 * 60 * 60 * 24) * days);
        }

        var res = [{
            "location": "us-west-2",
            "metadata": true,
            "name": "s3metadatademo",
            "last_access" : subDays(now, 10),
            "prices": [{
                "cost": 0.003,
                "provider": "aws"
            }, {
                "cost": 0.002,
                "provider": "gcloud"
            }, {
                "cost": 0.007,
                "provider": "azure"
            }],
            "provider": "aws",
            "type": "standard",
            "used_space": 123757682.06593406
        }, {
            "location": "us-west-2",
            "metadata": true,
            "name": "trackit-s3-logs",
            "last_access" : subDays(now, 30),
            "prices": [{
                "cost": 0.0,
                "provider": "aws"
            }, {
                "cost": 0.0,
                "provider": "gcloud"
            }, {
                "cost": 0.0,
                "provider": "azure"
            }],
            "provider": "aws",
            "type": "standard",
            "used_space": 859157.4285714285
        }, {
            "location": "us-west-2",
            "metadata": true,
            "name": "trackitelasticsnapshot",
            "last_access" : subDays(now, 3),
            "prices": [{
                "cost": 20.203,
                "provider": "aws"
            }, {
                "cost": 20.176,
                "provider": "gcloud"
            }, {
                "cost": 20.426,
                "provider": "azure"
            }],
            "provider": "aws",
            "type": "standard",
            "used_space": 1268686847.0
        }, {
            "location": "us-west-2",
            "metadata": true,
            "name": "trackit-billing-report",
            "last_access" : subDays(now, 20),
            "prices": [{
                "cost": 0.0,
                "provider": "aws"
            }, {
                "cost": 0.0,
                "provider": "gcloud"
            }, {
                "cost": 0.0,
                "provider": "azure"
            }],
            "provider": "aws",
            "type": "standard",
            "used_space": 3652982.25974026
        }, {
            "location": "us-west-2",
            "metadata": true,
            "name": "trackit-elb-logs",
            "last_access" : subDays(now, 33),
            "prices": [{
                "cost": 0.006,
                "provider": "aws"
            }, {
                "cost": 0.005,
                "provider": "gcloud"
            }, {
                "cost": 0.013,
                "provider": "azure"
            }],
            "provider": "aws",
            "type": "standard",
            "used_space": 229692236.52631578
        }, {
            "location": "us-east-1",
            "metadata": true,
            "name": "cf-templates-165mui4ksxr7k-us-east-1",
            "last_access" : subDays(now, 3),
            "prices": [{
                "cost": 0.0,
                "provider": "aws"
            }, {
                "cost": 0.0,
                "provider": "gcloud"
            }, {
                "cost": 0.0,
                "provider": "azure"
            }],
            "provider": "aws",
            "type": "standard",
            "used_space": 292421.0
        },
        {
              "location": "us-east-1",
              "metadata": false,
              "name": "trackit-attic",
              "last_access" : subDays(now, 10),
              "prices": [
                {
                  "cost": 8.344,
                  "provider": "aws"
                },
                {
                  "cost": 8.716,
                  "provider": "gcloud"
                },
                {
                  "cost": 8.292,
                  "provider": "azure"
                }
              ],
              "provider": "aws",
              "type": "standard",
              "used_space": 567943764.0
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "trackit-certs-us-east-1",
              "last_access" : subDays(now, 5),
              "prices": [
                {
                  "cost": 0.056,
                  "provider": "aws"
                },
                {
                  "cost": 0.048,
                  "provider": "gcloud"
                },
                {
                  "cost": 0.117,
                  "provider": "azure"
                }
              ],
              "provider": "aws",
              "type": "standard",
              "used_space": 287547987.75
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "trackit-dmarc",
              "prices": [
                {
                  "cost": 0.045,
                  "provider": "aws"
                },
                {
                  "cost": 0.039,
                  "provider": "gcloud"
                },
                {
                  "cost": 0.095,
                  "provider": "azure"
                }
              ],
              "provider": "aws",
              "type": "standard",
              "used_space": 123456789.3
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "trackit-replication-source",
              "last_access" : subDays(now, 3),
              "prices": [
                {
                  "cost": 12.407,
                  "provider": "aws"
                },
                {
                  "cost": 12.89,
                  "provider": "gcloud"
                },
                {
                  "cost": 1036.307,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 876954568.35
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "trackit-s3-logs",
              "last_access" : subDays(now, 3),
              "prices": [
                {
                  "cost":9.059,
                  "provider": "aws"
                },
                {
                  "cost":9.296,
                  "provider": "gcloud"
                },
                {
                  "cost": 9.859,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 678956897.6
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "trackit-tech-emails",
              "last_access" : subDays(now, 3),
              "prices": [
                {
                  "cost": 0.0,
                  "provider": "aws"
                },
                {
                  "cost": 0.0,
                  "provider": "gcloud"
                },
                {
                  "cost": 0.0,
                  "provider": "azure"
                }
              ],
              "provider": "aws",
              "type": "standard",
              "used_space": 24562.0
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "trackit_hashtags",
              "prices": [
                {
                  "cost": 0.0,
                  "provider": "aws"
                },
                {
                  "cost": 0.0,
                  "provider": "gcloud"
                },
                {
                  "cost": 0.0,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 68.0
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "obvious-trackit-datapipeline-backups",
              "last_access" : subDays(now, 10),
              "prices": [
                {
                  "cost": 1337.694,
                  "provider": "aws"
                },
                {
                  "cost": 8.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 555678987.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 10),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 10),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 10),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 10),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 10),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 10),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 10),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 10),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 10),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 10),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 4),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 4),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 4),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 4),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 4),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 4),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 4),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            },
            {
              "location": "us-east-1",
              "metadata": false,
              "name": "small-storage-container",
              "last_access" : subDays(now, 4),
              "prices": [
                {
                  "cost": 1.694,
                  "provider": "aws"
                },
                {
                  "cost": 0.533,
                  "provider": "gcloud"
                },
                {
                  "cost": 2833.525,
                  "provider": "azure"
                }
              ],
              "provider": "gcloud",
              "type": "standard",
              "used_space": 3200000.55
            }
      ];

        return res;
    };
});
