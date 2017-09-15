'use strict';

angular.module('trackit')
    .controller('S3MapCtrl', ['$scope', 'MapModel', '$sce', '$cookies', '$http', 'Config',
        function($scope, MapModel, $sce, $cookies, $http, Config) {


            var locations = [{
                name: "AWS GovCloud (US)",
                provider: "aws",
                position: "",
                used_space: [],
                location: {
                    long: -110.019531,
                    lat: 36.833850
                },
                items: []
            }, {
                name: "Asia Pacific (Seoul)",
                provider: "aws",
                position: "ap-northeast-2",
                used_space: [],
                location: {
                    long: 126.977969,
                    lat: 37.566535
                },
                items: []
            }, {
                name: "Asia Pacific (Singapore)",
                provider: "aws",
                position: "ap-southeast-1",
                used_space: [],
                location: {
                    long: 103.819836,
                    lat: 1.352083
                },
                items: []
            }, {
                name: "Asia Pacific (Sydney)",
                provider: "aws",
                position: "ap-southeast-2",
                used_space: [],
                location: {
                    long: 151.206990,
                    lat: -33.867487
                },
                items: []
            }, {
                name: "Asia Pacific (Tokyo)",
                provider: "aws",
                position: "ap-northeast-1",
                used_space: [],
                location: {
                    long: 139.691706,
                    lat: 35.689487
                },
                items: []
            }, {
                name: "EU (Frankfurt)",
                provider: "aws",
                position: "eu-central-1",
                used_space: [],
                location: {
                    long: 10.682127,
                    lat: 50.110922
                },
                items: []
            }, {
                name: "EU (Ireland)",
                provider: "aws",
                position: "eu-west-1",
                used_space: [],
                location: {
                    long: -8.243890,
                    lat: 53.412910
                },
                items: []
            }, {
                name: "South America (Sao Paulo)",
                provider: "aws",
                position: "sa-east-1",
                used_space: [],
                location: {
                    long: -46.633309,
                    lat: -23.550520
                },
                items: []
            }, {
                name: "US East (N. Virginia)",
                provider: "aws",
                position: "us-east-1",
                used_space: [],
                location: {
                    long: -75.410156,
                    lat: 40.380093
                },
                items: []
            }, {
                name: "US West (N. California)",
                provider: "aws",
                position: "us-west-1",
                used_space: [],
                location: {
                    long: -121.816406,
                    lat: 36.518466
                },
                items: []
            }, {
                name: "US West (Oregon)",
                provider: "aws",
                position: "us-west-2",
                used_space: [],
                location: {
                    long: -123.925781,
                    lat: 47.450380
                },
                items: []
            }, {
                name: "US East (South Carolina)",
                provider: "gcloud",
                position: "",
                used_space: [],
                location: {
                    long: -82.008775,
                    lat: 34.126062
                },
                items: []
            }, {
                name: "US Central (Iowa)",
                provider: "gcloud",
                position: "",
                used_space: [],
                location: {
                    long: -95.860833,
                    lat: 35.261944
                },
                items: []
            }, {
                name: "EU (Belgium)",
                provider: "gcloud",
                position: "",
                used_space: [],
                location: {
                    long: 0.818376,
                    lat: 50.449109
                },
                items: []
            }, {
                name: "Asia Pacific (Taiwan)",
                provider: "gcloud",
                position: "",
                used_space: [],
                location: {
                    long: 120.516135,
                    lat: 24.051796
                },
                items: []
            }, {
                name: "Japan",
                provider: "azure",
                position: "",
                used_space: [],
                location: {
                    long: 143.349609,
                    lat: 43.371116
                },
                items: []
            }, {
                name: "Hong Kong",
                provider: "azure",
                position: "",
                used_space: [],
                location: {
                    long: 109.379883,
                    lat: 21.523350
                },
                items: []
            }, {
                name: "Netherlands",
                provider: "azure",
                position: "",
                used_space: [],
                location: {
                    long: 5.291266,
                    lat: 55.132633
                },
                items: []
            }, {
                name: "Brazil",
                provider: "azure",
                position: "",
                used_space: [],
                location: {
                    long: -51.925280,
                    lat: -14.235004
                },
                items: []
            }, {
                name: "India",
                provider: "azure",
                position: "",
                used_space: [],
                location: {
                    long: 78.962880,
                    lat: 20.593684
                },
                items: []
            }, {
                name: "Singapore",
                provider: "azure",
                position: "",
                used_space: [],
                location: {
                    long: 99.843750,
                    lat: 9.400291
                },
                items: []
            }, {
                name: "Australia",
                provider: "azure",
                position: "",
                used_space: [],
                location: {
                    long: 134.121094,
                    lat: -24.891419
                },
                items: []
            }, {
                name: "Ireland",
                provider: "azure",
                position: "",
                used_space: [],
                location: {
                    long: -15.886719,
                    lat: 53.510918
                },
                items: []
            }, {
                name: "Canada",
                provider: "azure",
                position: "",
                used_space: [],
                location: {
                    long: -105.996094,
                    lat: 56.629042
                },
                items: []
            }, {
                name: "US",
                provider: "azure",
                position: "",
                used_space: [],
                location: {
                    long: -101.074219,
                    lat: 43.671845
                },
                items: []
            }];


            var awsSelectedKey = $cookies.getObject('awsKey');
            var gcSelectedKey = $cookies.getObject('gcKey');
            $scope.awsSelectedKey = awsSelectedKey;
            $scope.gcSelectedKey = gcSelectedKey;

            var locationsFilled = null;


            // used to know when to draw the map
            $scope.providersLoaded = 0;

            $scope.$watch('providersLoaded', function(newValue) {
                console.log('NEW PROVIDER LOADED');
                console.log(newValue);
                if (newValue) {
                    $scope.bestValueArchive = findBestValue(["Archive", "Nearline storage", "Cool Block Blob"]);
                    $scope.bestValueGeneral = findBestValue(["General Purpose", "Standard storage", "Hot Block Blob", "Standard storage disk"]);
                    $scope.bestValueInfrequent = findBestValue(["Infrequent Access", "DRA storage"]);
                    $scope.bestValueNonCritical = findBestValue("Non-Critical Data");
                    $scope.dataLoaded = true;
                    drawMarkers();
                }
            });

            var helpContent = {
                archive: {
                    helpText: 'High latency, highly durable storage for archiving, very low cost.',
                    includeText: ["AWS Archive (Glacier)", "Google Cloud Nearline", "Azure Cold Block Blob"]
                },
                general: {
                    helpText: 'Low latency, high durabilty, high availability, high performances.',
                    includeText: ["AWS General Purpose (Standard)", "Google Cloud Standard Storage", "Azure Hot Block Blob", "Azure Standard disk storage"]
                },
                infrequent: {
                    helpText: 'High durabilty, lower availability, high performances.',
                    includeText: ["AWS Infrequent Access", "Google DRA Storage"]
                },
                noncritical: {
                    helpText: 'Lower redundancy, for non-critical reproductible data',
                    includeText: ["AWS Non-Critical (Reduced redundancy)"]
                }
            };

            $scope.archiveHelpTemplate = getHelpTemplate(helpContent.archive);
            $scope.generalHelpTemplate = getHelpTemplate(helpContent.general);
            $scope.infrequentHelpTemplate = getHelpTemplate(helpContent.infrequent);
            $scope.noncriticalHelpTemplate = getHelpTemplate(helpContent.noncritical);


            function getHelpTemplate(help) {
                var res = '';

                res += '<h4>';
                res += help.helpText;
                res += '<hr>'
                res += '<ul>';
                for (var i = 0; i < help.includeText.length; i++) {
                    res += '<li>';
                    res += help.includeText[i];
                    res += '</li>';
                }
                res += '</ul>';
                res += '</h4>';


                return $sce.trustAsHtml(res);
            };



            $scope.slider = {
                value: 100,
                options: {
                    floor: 0,
                    ceil: 10000,
                    step: 20,
                    onEnd: function(sliderId, modelValue, highValue) {
                        console.log('ended');
                        $scope.providersLoaded = 0;

                        refreshData();
                    }
                }
            };

            function getLocationsTemplate(data) {
                var res = '';
                res += '<h4>Locations&nbsp;for&nbsp;best&nbsp;value&nbsp;</h4>';
                res += '<hr>';
                for (var i = 0; i < data.length; i++) {
                    if (data[i].provider == 'aws') {
                        res += '<h4><img class="valueIcon" src="img/s3-square.png"/>  ';
                    } else if (data[i].provider == 'gcloud') {
                        res += '<h4><img class="valueIcon" src="img/gc-square.png"/>  ';
                    } else {
                        res += '<h4>'
                    }


                    res += data[i].location + '</h4>';
                }
                return res;
            }

            function findBestValue(storageTypes) {
                var cost = 999999999999999999;
                var res = [];



                for (var i = 0; i < locationsFilled.length; i++) {
                    var parent = locationsFilled[i];
                    for (var j = 0; j < parent.items.length; j++) {
                        parent.items[j]

                        if (storageTypes.indexOf(parent.items[j].storageClass) != -1) {
                            if (parent.items[j].cost < cost) {
                                cost = parent.items[j].cost;
                                res = [];
                                parent.items[j].provider = parent.provider;
                                res.push(parent.items[j]);
                            } else if (parent.items[j].cost == cost) {
                                parent.items[j].provider = parent.provider;
                                res.push(parent.items[j]);
                            }
                        }

                    }
                }
                return {
                    data: res,
                    template: $sce.trustAsHtml(getLocationsTemplate(res))
                };
            }

            function getAWSData() {
                MapModel.getS3Pricing({
                    size: $scope.slider.value
                }, function(data) {
                    for (var i = 0; i < data.prices.length; i++) {
                        var tmp = data.prices[i];
                        if (getLocationIndex(tmp.location) != null) {
                            locationsFilled[getLocationIndex(tmp.location)].items.push(tmp);
                        }
                    }
                    $scope.providersLoaded++;

                }, function(data) {
                    console.log(data);
                })
            }

            function getGCData() {
                // GOOGLE CLOUD
                MapModel.getGCPricing({
                    size: $scope.slider.value
                }, function(dataGC) {
                    console.log(dataGC);

                    for (var i = 0; i < dataGC.prices.length; i++) {
                        var tmp = dataGC.prices[i];
                        if (getLocationIndex(tmp.location) != null) {
                            locationsFilled[getLocationIndex(tmp.location)].items.push(tmp);

                        }
                    }
                    $scope.providersLoaded++;
                }, function(dataGC) {
                    console.log(dataGC);
                });
            }

            function getAzureData() {
                MapModel.getAzurePricing({
                        size: $scope.slider.value
                    },
                    function(dataAzure) {
                        console.log(dataAzure);
                        for (var i = 0; i < dataAzure.prices.length; i++) {
                            var tmp = dataAzure.prices[i];
                            if (getLocationIndex(tmp.region) != null) {
                                locationsFilled[getLocationIndex(tmp.region)].items.push(tmp);
                            }
                        }

                        $scope.providersLoaded++;
                    },
                    function(dataAzure) {
                        console.log(dataAzure);
                    });
            }

            function refreshData() {
                $scope.dataLoaded = false;

                if (awsSelectedKey) {
                    $http.get(Config.apiUrl("/aws/accounts/" + $cookies.getObject('awsKey') + "/s3/space_usage"))
                        .success(function(data) {
                            if (data.buckets) {
                              $scope.buckets = data.buckets;
                            } else {
                              $scope.buckets = [];
                            }
                            console.log($scope.buckets);
                        })
                        .then(function successCallback() {
                            // Deep cloning the array
                            locationsFilled = jQuery.extend(true, [], locations);

                            // Pushing buckets info to locationsFilled
                            for (var j = 0; j < locationsFilled.length; j++) {
                                var tmp_res = locationsFilled[j];
                                for (var k = 0; k < $scope.buckets.length; k++) {
                                    var tmp_bucket = $scope.buckets[k];
                                    if (tmp_res.position == tmp_bucket.location) {
                                        locationsFilled[j].used_space.push({
                                            "used_space": tmp_bucket.used_space,
                                            "name": tmp_bucket.name
                                        });
                                    }
                                }
                            }

                            getAWSData();
                            getGCData();
                            getAzureData();

                        })
                } else {
                    // Deep cloning the array
                    locationsFilled = jQuery.extend(true, [], locations);


                    getAWSData();
                    getGCData();
                    getAzureData();
                }


            }
            refreshData();




            function getLocationIndex(nameOfLoc) {
                for (var i = 0; i < locationsFilled.length; i++) {
                    if (locationsFilled[i].name == nameOfLoc) {
                        return i;
                    }
                }
                return null;
            }


            var margin = {
                    top: 10,
                    left: 10,
                    bottom: 10,
                    right: 10
                },
                width = parseInt(d3.select('.world-map').style('width')),
                width = width - margin.left - margin.right,
                mapRatio = .8,
                height = width * mapRatio;

            d3.select(window).on('resize', resize);


            // RESIZE
            function resize() {
                console.log('resizing');

                // adjust things when the window size changes
                width = parseInt(d3.select('.world-map').style('width'));
                width = width - margin.left - margin.right;
                height = width * mapRatio;

                svg.attr("width", width)
                    .attr("height", height);
                // update projection
                projection = d3.geo.mercator()
                    .scale((width + 1) / 2 / Math.PI)
                    .translate([(width / 2), (height / 2.8)])
                    .precision(.1);

                geoPath = d3.geo.path()
                    .projection(projection);

                g.selectAll('path').attr('d', geoPath);


                markers.attr("transform", function(d) {
                    return "translate(" + projection([d.location.long, d.location.lat]) + ")";
                });



            }
            //END RESIZE



            // GEO
            var tooltipChartWidth = 250;
            var tooltipChartHeight = 100;
            var tooltipChartHeightMargin = 20;

            var svg = d3.select(".world-map")
                .append("svg")
                .attr("width", width)
                .attr("height", height);

            var g = svg.append("g");

            var projection = d3.geo.mercator()
                .scale((width + 1) / 2 / Math.PI)
                .translate([(width / 2), (height / 2.8)])
                .precision(.1);

            //GLOBE
            /*var projection = d3.geo.orthographic()
            .scale(475)
            .translate([width / 2, height / 2])
            .clipAngle(90)
            .precision(.1);*/


            var geoPath = d3.geo.path()
                .projection(projection);

            var map = g.selectAll("path")
                .data(worldJson.features)
                .enter()
                .append("path")
                .attr('class', 'country')
                .attr("fill", "#08C")
                .attr("d", geoPath);

            //END GEO



            // UTILITIES
            function getTotalRisks(item) {
                var t = item.tests;

                if (t) {
                    return t[1].count + t[2].count + t[3].count;
                }
            }


            function getMaxCount(items) {
                var res = 0;
                for (var i = 0; i < items.length; i++) {
                    if (items[i].count > res)
                        res = items[i].count;
                }
                return res;
            }

            function getMarkersRadius() {
                var min = 30; //min marker radius
                var max = 50; // max marker radius
                var maxRes = 1239; //max resolution
                var minRes = 900; //min acceptable resolution

                var resDiff = maxRes - minRes;
                var diff = max - min;


                var quotient = diff / resDiff;


                var thewidth = parseInt(d3.select('.world-map').style('width'));


                if (thewidth < minRes)
                    return min;
                else if (thewidth > maxRes) {
                    return max;
                } else {
                    return ((thewidth - minRes) * quotient) + min;
                }


            }

            function bytesToSize(bytes) {
                var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
                if (bytes == 0) return 'n/a';
                var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
                if (i == 0) return bytes + ' ' + sizes[i];
                return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i];
            }
            //END UTILITIES


            var arc = d3.svg.arc()
                .outerRadius(50);

            var color = d3.scale.ordinal()
                .range(['#359c10', '#95ac25', '#F98A00', '#bd1313', '#C3F25C']);

            var pie = d3.layout.pie()
                .value(function(d) {
                    return d.count;
                })
                .sort(null);

            var donutWidth = 10;
            var radius = 70;

            function drawMarkers() {

                markers = svg.selectAll(".mark")
                    .data(locationsFilled)
                    .enter()
                    .append("g")
                    .attr('class', 'mark')
                    .attr("transform", function(d) {
                        return "translate(" + projection([d.location.long - 3, d.location.lat + 2]) + ")";
                    }).on("mouseover", function(d) {
                        var parent = d3.transform(d3.select(this).attr("transform")).translate;

                        // Hack so the eastern location's tooltips don't display out of the window
                        if (d.name == "Asia Pacific (Sydney)" || d.name == "Australia" ||  d.name == "Japan" || d.name == "Asia Pacific (Tokyo)" || d.name == "Asia Pacific (Seoul)" ||  d.name == "Asia Pacific (Singapore)") {
                            tooltip.style("top", parent[1] - 220 + 'px').style("left", parent[0] - 340 + 'px');
                            s3tip.style("top", parent[1] - 220 + 'px').style("left", parent[0] - 730 + 'px');
                        } else if (d.name == "India" || d.name == "Hong Kong" || d.name == "Asia Pacific (Taiwan)" || d.name == "Singapore") {
                            tooltip.style("top", parent[1] + 50 + 'px').style("left", parent[0] - 60 + 'px');
                            s3tip.style("top", parent[1] + 50 + 'px').style("left", parent[0] - 450 + 'px');
                        } else if (d.name == "South America (Sao Paulo)") {
                            tooltip.style("top", parent[1] - 280 + 'px').style("left", parent[0] - 340 + 'px');
                            s3tip.style("top", parent[1] - 280 + 'px').style("left", parent[0] + 10 + 'px');
                        } else {
                            tooltip.style("top", parent[1] + 50 + 'px').style("left", parent[0] - 60 + 'px');
                            s3tip.style("top", parent[1] + 50 + 'px').style("left", parent[0] + 280 + 'px');
                        }


                        var tooltipTitleMarkup = "";

                        if (d.provider == 'gcloud')
                            tooltipTitleMarkup += '<img style="max-height: 70px;" class="logo" src="img/google-cloud-logo.png"/>';
                        else if (d.provider == 'aws')
                            tooltipTitleMarkup += '<img style="max-height: 50px;" class="logo" src="img/s3-logo.png"/>';
                        else if (d.provider == 'azure')
                            tooltipTitleMarkup += '<img style="max-height: 45px;" class="logo" src="img/ms-full-logo.png"/>';
                        tooltipTitleMarkup += '<h5 class="tooltip-title">' + d.name + '</h5>';


                        tooltipTitle.html(tooltipTitleMarkup);


                        var listHtml = '';

                        if (d.items) {
                            for (var i = 0; i < d.items.length; i++) {

                                listHtml += '<div style="border-top: 1px solid #c9c9c9; padding-top: 5px;">';
                                listHtml += '<p class="tooltip-storageClass"><strong>';
                                listHtml += d.items[i].storageClass;
                                listHtml += '</strong></p>';
                                listHtml += '<p class="tooltip-price"> $'
                                listHtml += parseFloat(d.items[i].cost).toFixed(2);
                                listHtml += '<span style="font-size: 10px;">/month</span></p>';
                                listHtml += '</div>';

                                listHtml += '<div style="clear: both;"></div>'

                                listHtml += '<div>';
                                listHtml += '<p style="float: left; margin-right: 20px;">Durability : ';
                                var durabilityFloat = parseFloat(d.items[i].durability.slice(0, -1));
                                if (d.items[i].durability == 'N/A') {
                                    listHtml += '<strong>N/A</strong>';
                                } else {
                                    if (durabilityFloat >= 99)
                                        listHtml += '<i class="fa fa-check-circle green"></i>'
                                    else
                                        listHtml += '<i class="fa fa-times red"></i>'
                                }
                                listHtml += '</p>';
                                listHtml += '<p style="float: left;">Availability : ';
                                if (d.items[i].availability == 'N/A') {
                                    listHtml += '<strong>N/A</strong>';
                                } else {
                                    var availabilityFloat = parseFloat(d.items[i].availability.slice(0, -1));
                                    if (availabilityFloat >= 99)
                                        listHtml += '<i class="fa fa-check-circle green"></i>'
                                    else
                                        listHtml += '<i class="fa fa-times red"></i>'
                                }
                                listHtml += '</p>';

                                listHtml += '</div>';
                                listHtml += '<div style="clear: both;"></div>';

                            }

                            var data = [];
                            var chartHtml = '';
                            if (d.used_space.length > 0) {
                                chartHtml = "<div class='s3-title'>Current S3 space usage</div>";
                                chartHtml += "<div style='border-top: 1px solid #c9c9c9; padding-top: 5px;'>";
                                chartHtml += "<div class='chart s3-chart'><svg></svg></div>";
                                for (var k = 0; k < d.used_space.length; k++) {
                                    data.push({
                                        "value": d.used_space[k].used_space,
                                        "label": d.used_space[k].name
                                    });
                                }
                            }

                            nv.addGraph(function() {
                                var chart = nv.models.pieChart()
                                    .x(function(d) {
                                        return d.label
                                    })
                                    .y(function(d) {
                                        return d.value
                                    })
                                    .donut(true)
                                    .donutRatio(0.35)
                                    .width(420)
                                    .height(420)
                                    .padAngle(.03)
                                    .showLegend(false)
                                    .showLabels(false);

                                chart.tooltip.contentGenerator(function(d) {
                                    var html = '';
                                    d.series.forEach(function(elem) {
                                        html += "<p style='color:" + elem.color + "; padding: 3px 3px 0px;'>" + elem.key + "</p><p><b>" + bytesToSize(elem.value) + "</b></p>";
                                    });
                                    return html;
                                });

                                d3.select(".chart svg")
                                    .datum(data)
                                    .transition().duration(1200)
                                    .call(chart);

                                return chart;
                            });
                        }

                        s3tip.html(chartHtml);
                        tooltipList.html(listHtml);

                        tooltip.style('display', 'block');
                        tooltip.transition()
                            .duration(400)
                            .style("opacity", .95);
                        if (d.used_space.length > 0) {
                            s3tip.style('display', 'block');
                            s3tip.transition()
                                .duration(400)
                                .style("opacity", .95);
                        } else {
                            s3tip.transition()
                                .duration(200)
                                .style("opacity", 0);
                            s3tip.html('');
                        }

                    })
                    /*.on("mouseout", function(d) {
                        tooltip.style("top", -2000 + 'px').style("left", -2000 + 'px');

                        tooltip.transition()
                            .duration(200)
                            .style("opacity", 0);
                        tooltipTitle.html('');

                        s3tip.style("top", -2000 + 'px').style("left", -2000 + 'px');

                        s3tip.transition()
                            .duration(200)
                            .style("opacity", 0);
                        s3tip.html('');

                    });*/


                // Draw circle for consistent hovering
                var circle = markers.append('circle')
                    .attr('r', 20)
                    .attr("transform", "translate(" + 15 + "," + 15 + ")")
                    .style("fill", function(d) {
                        if (d.used_space.length > 0)
                            return "rgb(3, 39, 99)";
                        else
                            return "rgb(207, 206, 206)";
                    })
                    .style("fill-opacity", .8);

                // Draw icon on location
                /*var icon = markers.append("svg")
                    .attr("width", 40)
                    .attr("height", 40)
                    .attr("xml:space", "preserve")
                    .attr("viewBox", "0 0 823 823")
                    .attr("style", "enable-background:new 0 0 823 823;");

                icon.append("path")
                    .attr("d", "M411.5,823c210.4,0,381-48.4,381-108V578.8c-2.5,1.9-5,3.7-7.699,5.5c-22.701,15.2-54,28.5-93,39.601    C616.4,645.2,516.9,657,411.5,657c-105.4,0-204.9-11.8-280.3-33.1c-39-11.101-70.3-24.4-93-39.601c-2.7-1.8-5.2-3.6-7.7-5.5V715    C30.5,774.6,201.101,823,411.5,823z")
                    .attr("fill", "#fff");

                icon.append("path")
                    .attr("d", "M411.5,617c203.3,0,369.4-45.1,380.4-102c0.4-2,0.6-4,0.6-6V371.8c-2.5,1.9-5,3.7-7.699,5.5    c-19.1,12.8-44.4,24.3-75.301,34.2c-5.699,1.8-11.6,3.6-17.699,5.4c-6.1,1.699-12.301,3.399-18.701,5    c-14.799,3.699-30.299,7-46.5,10C562.9,443.7,488.801,450,411.5,450c-77.3,0-151.4-6.3-215.2-18.1c-16.2-3-31.7-6.4-46.5-10    c-6.4-1.601-12.6-3.2-18.7-5c-6.1-1.7-12-3.5-17.7-5.4c-30.9-9.9-56.2-21.4-75.3-34.2c-2.7-1.8-5.2-3.6-7.7-5.5V509    c0,2,0.2,4,0.6,6C42.101,571.9,208.201,617,411.5,617z")
                    .attr("fill", "#fff");

                icon.append("path")
                    .attr("d", "M196.3,391.1c20.7,4,42.8,7.5,66.101,10.301c45.8,5.5,96.199,8.6,149.1,8.6c52.9,0,103.3-3.1,149.099-8.6    C583.9,398.6,606,395.1,626.701,391.1c94.199-18.3,158-48.3,165.199-82.6c0.5-2.2,0.699-4.3,0.699-6.5V108    c0-59.6-170.6-108-381-108c-210.399,0-381,48.4-381,108v194c0,2.2,0.2,4.3,0.7,6.5C38.4,342.8,102.101,372.8,196.3,391.1z     M452.5,308.3c0,22.601-18.4,41-41,41c-22.6,0-41-18.399-41-41c0-22.6,18.4-41,41-41C434.1,267.3,452.5,285.7,452.5,308.3z")
                    .attr("fill", "#fff");*/

                var icon = markers.append("svg:image")
                    .attr("width", 30)
                    .attr("height", 30)
                    .attr("xlink:href", function(d) {
                        if (d.provider == "aws")
                            return "img/s3-square.png";
                        else if (d.provider == "gcloud")
                            return "img/gc-square.png";
                        else if (d.provider == "azure")
                            return "img/ms-square.png";
                    });


            }

            var tooltip = d3.selectAll('.world-map')
                .append('div')
                .attr('class', 'world-map-tooltip')
                .style('display', 'none')
                .style('opacity', 0);

            var tooltipClose = tooltip.append('div')
                .attr('class', 'tooltip-close');

            tooltipClose.on("click", function() {
                console.log("rect");
                tooltip.style("top", -2000 + 'px').style("left", -2000 + 'px');

                tooltip.transition()
                    .duration(200)
                    .style("opacity", 0);
                tooltipTitle.html('');

                s3tip.style("top", -2000 + 'px').style("left", -2000 + 'px');

                s3tip.transition()
                    .duration(200)
                    .style("opacity", 0);
                s3tip.html('');
            });

            var tooltipTitle = tooltip.append('div')
                .attr('class', 'tooltip-title');

            var tooltipList = tooltip.append("div")
                .attr("class", 'tooltip-list');


            var s3tip = d3.selectAll('.world-map')
                .append('div')
                .attr('class', 'world-map-s3tip')
                .style('display', 'none')
                .style('opacity', 0);

            var wtooltip = d3.selectAll('.world-map-tooltip');
            var map = d3.selectAll('.world-map');
            wtooltip.on("mouseout", function() {
                map.on("click", function() {
                    tooltip.style("top", -2000 + 'px').style("left", -2000 + 'px');

                    tooltip.transition()
                        .duration(200)
                        .style("opacity", 0);
                    tooltipTitle.html('');

                    s3tip.style("top", -2000 + 'px').style("left", -2000 + 'px');

                    s3tip.transition()
                        .duration(200)
                        .style("opacity", 0);
                    s3tip.html('');
                });

            });

        }
    ]);
