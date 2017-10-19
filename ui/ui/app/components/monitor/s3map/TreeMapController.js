'use strict';

angular.module('trackit.statistics')
    .controller('TreeMapController', ['$scope', 'EstimationModel', '$cookies', '$filter', 'BillModel', '$uibModal', 'TreemapMockFactory', 'apiBaseUrl', '$http', 'AWSKey',
        function($scope, EstimationModel, $cookies, $filter, BillModel, $uibModal, TreemapMockFactory, apiBaseUrl, $http, AWSKey) {

            $scope.hoveredBucket = {};

            // Color scheme to colorate map from access data
            var mapColorScheme = {
                default: "#0088CC",
                light: "#81C784",
                medium: "#FFB74D",
                hard: "#E65100"
            };
            $scope.mapColorScheme = mapColorScheme;

            AWSKey.getMutipleKeysInfos({
                id: $cookies.getObject('awsKey')
            }, (data) => {
                console.log(data);
            });

            $http({
                method: 'GET',
                url: apiBaseUrl + '/aws/accounts/' + $cookies.getObject('awsKey')
            }).then(function successCallback(response) {
                if (response.data.key == "AKIAJNHPWPBV44OM3YUQ") {
                    $scope.demoMode = true;
                }
                startGettingData();
            }, function errorCallback(response) {
                console.log(response);
                startGettingData();
            });


            function parseMostUsedChart(data)  {
                var res = [];

                for (var i = 0; i < data.length; i++) {
                    var tmp = {};
                    tmp.label = data[i].object;
                    tmp.value = data[i].access_count;
                    res.push(tmp);
                }

                $scope.mostUsedData = [{
                    key: "Most Accessed Objects",
                    values: res
                }];
            };

            BillModel.getS3MostUsed({
                id: $scope.awsSelectedKey
            }, function(data) {
                $scope.mostUsed = data.objects;
                parseMostUsedChart($scope.mostUsed);

            }, function(data) {
                console.log(data);
            });



            $scope.mostUsedOptions = {
                chart: {
                    type: 'discreteBarChart',
                    height: 450,
                    margin: {
                        top: 20,
                        right: 20,
                        bottom: 150,
                        left: 55
                    },
                    x: function(d) {
                        return d.label;
                    },
                    y: function(d) {
                        return d.value;
                    },
                    showValues: true,
                    hideLabels: true,
                    rotateLabels: 33,
                    valueFormat: function(d) {
                        return d3.format(',.0f')(d);
                    },
                    duration: 500,
                    yAxis: {
                        axisLabel: 'Requests',
                        axisLabelDistance: -4
                    }
                }
            };

            // Check if location already exists in res
            function getLocationIndex(toSearch, location) {
                for (var i = 0; i < toSearch.length; i++) {
                    if (toSearch[i].name == location)
                        return i;
                }
                return -1;
            }

            // Ordering buckets by location objects
            function processBuckets() {
                var res = [];

                // ordering each bucket in its corresponding location filtering by maxDisplaySize
                for (var i = 0; i < $scope.buckets.length; i++) {
                    var tmp = $scope.buckets[i];
                    var tmpIndex = getLocationIndex(res, tmp.location);

                    if (tmp.used_space <= $scope.maxDisplaySize) {
                        // Already exists in res
                        if (tmpIndex >= 0) {
                            res[tmpIndex].children.push(tmp);
                        }
                        // Don't exist yet
                        else {
                            res.push({
                                "name": tmp.location,
                                "children": [
                                    tmp
                                ]
                            });
                        }
                    }


                }
                return res;
            }

            $scope.setHovered = function(item) {
                console.log(item);
                $scope.hoveredBucket.name = item.name;
                $scope.hoveredBucket.price = getCostForProvider(item.provider, item.prices);
                $scope.hoveredBucket.used_space = item.used_space;
                $scope.hoveredBucket.provider = item.provider;
                $scope.hoveredBucket.location = item.location;
                $scope.hoveredBucket.type = item.type;
                $scope.hoveredBucket.metadata = item.metadata;

                if (item.last_access)
                    $scope.hoveredBucket.last_access = item.last_access;

                $scope.$apply();
            }

            $scope.showStorageTreeModal = function(sto) {
                console.log(sto);
                var modalInstance = $uibModal.open({
                    templateUrl: 'components/optimize/costestimation/storageTree.html',
                    controller: 'StorageTreeController',
                    scope: $scope.$new(true),
                    windowClass: 'storage-tree-modal',
                    resolve: {
                        selectedPath: function() {
                            return sto;
                        }
                    }
                });
            };

            // Get min and max size values in buckets
            function getMinMax(buckets) {
                var res = {
                    min: 0,
                    max: 0
                };

                for (var i = 0; i < buckets.length; i++) {
                    var tmp = buckets[i];
                    if (tmp.used_space > res.max)
                        res.max = tmp.used_space;
                }
                res.min = res.max;
                for (var i = 0; i < buckets.length; i++) {
                    var tmp = buckets[i];
                    if (tmp.used_space < res.min)
                        res.min = tmp.used_space;
                }
                return res;
            }

            // Add access data to current data (dirty way to do it for now, should be improved or removed)
            function addAccessToData(basicData, accessData) {

                // Looping through access infos
                for (var i = 0; i < accessData.length; i++) {
                    var accessObject = accessData[i];
                    // Looping through locations
                    for (var j = 0; j < basicData.children.length; j++) {
                        var childrens = basicData.children[j].children;
                        // Looping through buckets
                        for (var k = 0; k < childrens.length; k++) {
                            if (childrens[k].name == accessObject.bucket_name) {
                                basicData.children[j].children[k].last_access = accessObject.last_access;
                            }
                        }
                    }
                }
                console.log(basicData);
                $scope.data = basicData;
            }

            // Return cost for corresponding provider in arr
            function getCostForProvider(provider, arr) {
                if (arr)
                    for (var i = 0; i < arr.length; i++) {
                        if (arr[i].name == provider || arr[i].provider == provider)
                            return arr[i].cost;
                    }
            }

            // Shade or lighten an hex color , percent param range from -1.0 to 1.0
            function shadeColor(color, percent) {
                var f = parseInt(color.slice(1), 16),
                    t = percent < 0 ? 0 : 255,
                    p = percent < 0 ? percent * -1 : percent,
                    R = f >> 16,
                    G = f >> 8 & 0x00FF,
                    B = f & 0x0000FF;
                return "#" + (0x1000000 + (Math.round((t - R) * p) + R) * 0x10000 + (Math.round((t - G) * p) + G) * 0x100 + (Math.round((t - B) * p) + B)).toString(16).slice(1);
            }

            // Launching dataget depending of demo mode enabled or not
            function startGettingData() {
                // Getting real data
                if (!$scope.demoMode) {
                    /*AWS Storage */
                    EstimationModel.getS3Estimation({
                        id: $cookies.getObject('awsKey')
                    }, function(data) {
                        console.log(data);
                        $scope.buckets = data.buckets;
                        // Getting min and max size values and setting limit to max
                        var minMax = getMinMax($scope.buckets);
                        $scope.maxDisplaySize = minMax.max;

                        $scope.data = {
                            "name": "storage",
                            "children": processBuckets()
                        };


                        // Get last access for map coloration
                        BillModel.getS3LastAccessed({
                            id: $scope.awsSelectedKey
                        }, function(data) {
                            if (data.objects.length) {
                                $scope.last_buckets = data.objects;
                                addAccessToData($scope.data, $scope.last_buckets);
                                if ($scope.data.children)
                                    drawTreeMap();
                            } else {
                                if ($scope.data.children)
                                    drawTreeMap();
                            }
                        }, function(data) {
                            console.log(data);
                        });

                    }, function(data) {
                        console.log(data);
                    });
                } else {
                    // GETTING DEMO data
                    // Used to set demo data instead of real data
                    // Async imitation
                    setTimeout(() => {
                        // MOCK DATA
                        var mockData = new TreemapMockFactory();
                        console.log(mockData);
                        $scope.buckets = mockData;

                        var minMax = getMinMax($scope.buckets);
                        $scope.maxDisplaySize = minMax.max;

                        $scope.data = {
                            "name": "storage",
                            "children": processBuckets()
                        };
                        if ($scope.data.children)
                            drawTreeMap();
                    }, 1000);
                }

            }









            var wrapper = document.getElementById("treemapWrapper");
            var chartPadding = 60;


            var w = wrapper.offsetWidth - chartPadding,
                h = 650,
                x = d3.scale.linear().range([0, w]),
                y = d3.scale.linear().range([0, h]),
                color = d3.scale.category20c(),
                root,
                node;

            /*color = d3.scale.ordinal()
            .range(["#0088CC", "#62ddf7"]);*/

            var treemap = d3.layout.treemap()
                .round(false)
                .size([w, h])
                .sticky(true)
                .value(function(d) {
                    return d.used_space;
                });

            var svg = d3.select("#treeMap").append("div")
                .attr("class", "chart")
                .style("width", w + "px")
                .style("height", h + "px")
                .append("svg:svg")
                .attr("width", w)
                .attr("height", h)
                .append("svg:g")
                .attr("transform", "translate(.5,.5)");



            function drawTreeMap() {
                console.log('DRAWING');
                node = root = $scope.data;
                //console.log(root);

                var nodes = treemap.nodes(root)
                    .filter(function(d) {
                        return !d.children;
                    });

                var cell = svg.selectAll("g")
                    .data(nodes);


                cell.enter().append("svg:g")
                    .attr("class", function(d) {
                        if (d.metadata)
                            return 'cell clickable';
                        else {
                            return 'cell';
                        }
                    })
                    .attr("transform", function(d) {
                        return "translate(" + d.x + "," + d.y + ")";
                    })
                    .on("click", function(d) {
                        console.log(d);
                        $scope.showStorageTreeModal(d.name);
                        d3.event.stopPropagation();
                    });



                cell.append("svg:rect")
                    .attr("width", function(d) {
                        return (d.dx - 1) >= 0 ? d.dx - 1 : 0;
                    })
                    .attr("height", function(d) {
                        return (d.dy - 1) >= 0 ? d.dy - 1 : 0;
                    })
                    .attr('class', 'treemap')
                    .style("fill", function(d) {
                        if (!d.last_access || d.last_access == "never_accessed") {
                            //return color(d.parent.last_access);
                            return mapColorScheme.default;
                        } else {
                            var itemDate = new Date(d.last_access);
                            // Find the difference between item date and now
                            var dayDiff = Math.floor((Date.now() - itemDate) / (1000 * 60 * 60 * 24));
                            if (dayDiff < 7)
                                return mapColorScheme.light;
                            else if (dayDiff > 7 && dayDiff < 30)
                                return mapColorScheme.medium;
                            else {
                                return (mapColorScheme.hard);
                            }
                        }
                    })
                    .style("stroke", "white")
                    .on("mouseover", function(d) {
                        console.log('HOVERED');
                        //appendTooltip(d);
                        $scope.setHovered(d);
                    })
                    .on("mouseout", function(d) {
                        //hideTooltip();
                        //$scope.hoveredBucket = {};
                    });

                cell.append("svg:text")
                    .attr("x", function(d) {
                        return d.dx / 2;
                    })
                    .attr("y", function(d) {
                        return d.dy / 2;
                    })
                    .attr("dy", ".35em")
                    .attr("text-anchor", "middle")
                    .text(function(d) {
                        return d.name + ' [' + $filter('bytes')(d.used_space) + ']';
                    })
                    .style("display", function(d) {
                        d.w = this.getComputedTextLength();
                        return d.dx + 10 > d.w ? 'block' : 'none';
                    })
                    .style("text-decoration", function(d) {
                        if (d.metadata)
                            return 'underline';
                        else {
                            return 'none';
                        }
                    })
                    .style("fill", "white")
                    .on("mouseover", function(d) {
                        //appendTooltip(d);
                        $scope.setHovered(d);
                    });


                d3.select(window).on("click", function() {
                    zoom(root);
                });

                function size(d) {
                    return d.used_space;
                }


                function zoom(d) {
                    var kx = w / d.dx,
                        ky = h / d.dy;

                    x.domain([d.x, d.x + d.dx]);
                    y.domain([d.y, d.y + d.dy]);

                    var t = svg.selectAll("g.cell").transition()
                        .duration(d3.event.altKey ? 7500 : 750)
                        .attr("transform", function(d) {
                            return "translate(" + x(d.x) + "," + y(d.y) + ")";
                        });

                    t.select("rect")
                        .attr("width", function(d) {
                            return kx * d.dx;
                        })
                        .attr("height", function(d) {
                            return ky * d.dy;
                        })

                    t.select("text")
                        .attr("x", function(d) {
                            return kx * d.dx / 2;
                        })
                        .attr("y", function(d) {
                            return ky * d.dy / 2;
                        })
                        .style("opacity", function(d) {
                            return kx * d.dx > d.w ? 1 : 0;
                        });

                    node = d;
                    d3.event.stopPropagation();
                }

                function appendTooltip(d) {
                    tooltip.style("top", d.y + 230 + 'px').style("left", d.x + d.dx + 340 + 'px');

                    var tooltipTitleMarkup = '';

                    if (d.provider == 'gcloud')
                        tooltipTitleMarkup += '<img style="max-height: 55px;" class="logo" src="img/google-cloud-logo.png"/>';
                    else if (d.provider == 'aws')
                        tooltipTitleMarkup += '<img style="max-height: 50px;" class="logo" src="img/s3-logo.png"/>';
                    else if (d.provider == 'azure')
                        tooltipTitleMarkup += '<img style="max-height: 35px;" class="logo" src="img/ms-full-logo.png"/>';
                    tooltipTitleMarkup += '<h5 class="tooltip-title" style="font-size: 17px;">' + d.name + '</h5>';

                    tooltipTitle.html(tooltipTitleMarkup);

                    var tooltipMarkup = '';

                    tooltipMarkup += '<span class="badge">';
                    tooltipMarkup += d.location;
                    tooltipMarkup += '</span>';

                    tooltipMarkup += '<h4>';
                    tooltipMarkup += $filter('currency')(getCostForProvider(d.provider, d.prices)) + '/mth';
                    tooltipMarkup += '</h4>';

                    tooltipMarkup += '<h4>';
                    tooltipMarkup += $filter('bytes')(d.used_space) + ' used';
                    tooltipMarkup += '</h4>';

                    tooltipContent.html(tooltipMarkup);

                    tooltip.style('display', 'block');
                    tooltip.transition()
                        .duration(400)
                        .style("opacity", .95);
                }

                function hideTooltip() {
                    tooltip.style("top", -2000 + 'px').style("left", -2000 + 'px');

                    tooltip.transition()
                        .duration(200)
                        .style("opacity", 0);
                    tooltipTitle.html('');
                }

                var tooltip = d3.select('#treeMap')
                    .append('div')
                    .attr('class', 'treemap-tooltip')
                    .style('display', 'none')
                    .style('opacity', 0);

                var tooltipTitle = tooltip.append('div')
                    .attr('class', 'tooltip-title');

                var tooltipContent = tooltip.append('div');
            }




        }
    ]);
