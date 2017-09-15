'use strict';

angular.module('trackit.prediction')


.controller('ResPredCtrl', ['$scope', 'EstimationModel', '$cookies',
    function($scope, EstimationModel, $cookies) {
        var now = new Date();
        $scope.dataPred = false;

        function backInTime(base, daysToRemove) {
            var tmp = base.getTime();
            var oneDay = 86400000;

            return (new Date(tmp - (oneDay * daysToRemove * 30)));
        }

        function backToTheFuture(base, daysToAdd) {
            var tmp = base.getTime();
            var oneDay = 86400000;

            return (new Date(tmp + (oneDay * daysToAdd * 30)));
        }

        function getPredicted(number) {
            return (number - ((number / 100) * 35));
        }


        EstimationModel.getPrediction({id: $cookies.getObject('awsKey')}, function(c) {
            if ('message' in c) {
              $scope.awsPredictionNoDataMessage = c.message;
              return;
            }
            $scope.awsPredictionNoDataMessage = null;
            var bestReservedMonths = {};
            var ondemandMonths = {};
            c.instances.forEach(function(type) {
                var alreadyFoundReserved = false;
                type.pricing_options.forEach(function(option) {
                    var sink = null;
                    if (option.reservationYears == 3 && option.upfrontCost > 0 && !alreadyFoundReserved) {
                        sink = bestReservedMonths;
                        alreadyFoundReserved = true;
                    } else if (option.type == 'ondemand') {
                        sink = ondemandMonths;
                    } else {
                        return;
                    }

                    option.months.forEach(function(month) {
                        sink[month.month] = (sink[month.month] || 0) + month.cost;
                    });
                });
            });

            //Confidence Interval 90% confidence level
            var confidenceLevel = 0.165;
            var marginOfError;
            var reserved = [];
            var ondemand = [];
            var suggested = [];
            var now = new Date();
            for (var monthStr in bestReservedMonths) {
                if (!bestReservedMonths.hasOwnProperty(monthStr)) { continue; }
                var monthParts = monthStr.split('-');
                var month = new Date(parseInt(monthParts[0]), parseInt(monthParts[1], 10));
                reserved.push({x: month, y: bestReservedMonths[monthStr]});
                ondemand.push({x: month, y: ondemandMonths[monthStr]});
            }

            reserved.sort(sortFunction);
            ondemand.sort(sortFunction);

            var suggested_extrapolated = [];
            function ondemand_to_suggested(p) {
                var shortMonth = p.x.toISOString().slice(0, 7);
                var longMonth = (
                    Object.keys(c['reduced_instance_costs']).concat(
                    Object.keys(c['volume_monthly_costs']))
                ).find(function(q) {
                    return q.startsWith(shortMonth);
                });
                if (c['reduced_instance_costs'][longMonth] === undefined
                    && c['volume_monthly_costs'][longMonth] === undefined) {
                    suggested_extrapolated.push(p);
                    return null;
                } else {
                    return {
                        reserved: p,
                        x: p.x,
                        y: p.y -
                           (c['reduced_instance_costs'][longMonth] * 4 || 0) - // Multiply by 4 as the API returns 20% of the cost, so we get 80% for substracting
                           (c['volume_monthly_costs'][longMonth] || 0)
                    };
                }
            }

            suggested = reserved.map(ondemand_to_suggested);
            suggested = suggested.filter(function(e) { return e !== null; });
            var suggested_reserved_ratio = suggested.map(function(s) {
                return s.y / s.reserved.y;
            });
            var mean_suggested_reserved_ratio = 1;
            if (suggested_reserved_ratio.length > 0)
                mean_suggested_reserved_ratio = suggested_reserved_ratio.reduce(function(a, b) {
                    return a + b;
                }) / suggested_reserved_ratio.length;
            suggested_extrapolated.forEach(function(p) {
                suggested.push({
                    reserved: p,
                    x: p.x,
                    y: p.y * mean_suggested_reserved_ratio,
                });
            });

            suggested.sort(sortFunction);

            $scope.dataPrediction = [];
            for (var i= 0; i < reserved.length; i++) {
                var date = reserved[i].x;
                if (new Date(date) >= now) {
                    marginOfError = confidenceLevel * reserved[i].y;
                    $scope.dataPrediction.push([new Date(date),
                        [ondemand[i].y, ondemand[i].y, ondemand[i].y],
                        [reserved[i].y - marginOfError, reserved[i].y, reserved[i].y + marginOfError],
                        [suggested[i].y - marginOfError, suggested[i].y, suggested[i].y + marginOfError],
                    ]);
                }
                else if (new Date(date).getMonth() == now.getMonth()) {
                    $scope.dataPrediction.push([new Date(date),
                        [ondemand[i].y, ondemand[i].y, ondemand[i].y],
                        [reserved[i].y, reserved[i].y, reserved[i].y],
                        [suggested[i].y, suggested[i].y, suggested[i].y],
                    ]);
                }
                else {
                    $scope.dataPrediction.push([new Date(date),
                        [ondemand[i].y, ondemand[i].y, ondemand[i].y],
                        [null, reserved[i].y, null],
                        [null, suggested[i].y, null],
                    ]);
                }
            }

            if ($scope.dataPrediction.length > 0) {
                $scope.dataPred = true;
                document.getElementById("graphdiv").style.display = 'block';
                new Dygraph(document.getElementById("graphdiv"),
                    $scope.dataPrediction,
                    {
                        errorBars: true,
                        animatedZooms: false,
                        customBars: true,
                        legend: 'always',
                        labelsSeparateLines: true,
                        axisLabelFontSize: '12',
                        labels: [
                            "x",
                            "Current costs",
                            "Predicted cost by switching to reserved instance",
                            "Predicted cost by following all suggestions",
                        ],
                        labelsDivWidth: "440",
                        colors: ["#1f77b4", "#ff9f4a", "#02a7cd"],
                        axes: {
                            y: {
                                axisLabelFormatter: function (y) {
                                    return "$" + y.toFixed(2);
                                },
                                valueFormatter: function (y) {
                                    return "$" + y.toFixed(2);
                                }
                            }
                        }
                    });
            }
            else {
                document.getElementById("graphdiv").style.display = 'none';
            }

            function sortFunction(a, b) {
                if (Date.parse(a.x) === Date.parse(b.x)) {
                    return 0;
                }
                else {
                    return (Date.parse(a.x) < Date.parse(b.x)) ? -1 : 1;
                }
            }


       /* $scope.data = [{
                key: 'Current costs',
                values: ondemand
            }, {
                key: 'Predicted costs',
                values: reserved
            }];*/
        });


        function getMaxValue(data) {
            var res = 0;

            for (var i = 0; i < data.length; i++) {
                if (parseInt(data[i].y) > res)
                    res = data[i].y;
            }
            return res;
        }

       /* $scope.options = {
            chart: {
                type: 'lineChart',
                height: 400,
                margin: {
                    top: 20,
                    right: 20,
                    bottom: 45,
                    left: 85
                },
                showControls: false,
                clipEdge: false,
                duration: 500,
                stacked: false,
                xAxis: {
                    axisLabel: 'Month',
                    tickFormat: function(d) {
                        return d3.time.format('%B %y')(new Date(d / 1))
                    }
                },
                yAxis: {
                    axisLabel: 'Cost',
                    axisLabelDistance: 20,
                    tickFormat: function(d) {
                        return '$' + d3.format(',.2f')(d)
                    }
                }
            }
        };*/


    }
]);

/* vim: set ts=4 sts=4 et: */
