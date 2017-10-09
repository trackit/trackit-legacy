'use strict';

angular.module('trackit.prediction')
  .directive('inspireTree', ['$q', '$parse', '$timeout', function($q, $parse, $timeout) {
    return {
      scope: {
        inspireTree: '&',
        selected: '=',
        selectedId: '='
      },
      link: function link(scope, element, attrs) {
        var tree = null;

        scope.$watch(attrs.selectedId, function(value) {
          if (tree) {
            var node = tree.node(value)
            if (node) {
              node.select();
            }
          }
        });

        buildTree();

        element.on('$destroy', destroyTree);

        function destroyTree() {
          tree = null;
        }

        function buildTree() {
          destroyTree();
          var selectedId = scope.selectedId;
          tree = new InspireTree({
            target: element[0],
            data: function(node, resolve, reject) {
              try {
                var promise = scope.inspireTree()(node);
              } catch(e) {
                console.error(e);
                return;
              }
              promise.then(function(res, err) {
                if (res || !err) {
                  resolve(res);
                  if (selectedId && tree) {
                    $timeout(function() {
                      tree.node(selectedId).select();
                      selectedId = null;
                    });
                  }
                } else {
                  reject(err);
                }
              });
            }
          });

          tree.on('node.selected', function(node) {
            scope.selected = node;
            scope.selectedId = node ? node.id : null;
            $timeout(function() {
              scope.$apply();
            });
          });
        }
      }
    };
  }])
  .controller('StorageTreeController', ['$uibModalInstance', '$scope', 'EstimationModel', '$cookies', 'selectedPath',
    function($uibModalInstance, $scope, EstimationModel, $cookies, selectedPath) {
        $scope.ok = function() {
            $uibModalInstance.dismiss();
        };

        $scope.selectedId = selectedPath;
        $scope.filterTag = '';
        $scope.tagKey = '';
        $scope.metadataLoaded = false;
        $scope.tags = [];
        $scope.tagKeys = [];

        $scope.$watch('selectedId', loadMetadata);
        $scope.$watch('filterTag', loadMetadata,true);
        $scope.$watch('tagKey', loadMetadata,true);

        var loaded = '';
        function loadMetadata() {
          var loaded_ = JSON.stringify([$scope.selectedId, $scope.filterTag, $scope.tagKey]);
          if (loaded == loaded_) { return; }
          loaded = loaded_;
          $scope.metadataLoaded = false;
          var args = {id: $cookies.getObject('awsKey'), path: $scope.selectedId};
          if ($scope.filterTag) {
            args.tag = $scope.filterTag;
          }
          if ($scope.tagKey) {
            args.tagkey = $scope.tagKey;
          }
          EstimationModel.getS3SpaceUsageTags(args).$promise.then(function(res) {
            $scope.tags = [''].concat(Object.keys(res.tags));
            $scope.tagKeys = [''].concat(res.keys);
            if ($scope.tagKey) {
              $scope.metadata = formatVals(res.tags, 12, $scope.tagKey + '=other');
              stripTagKey($scope.metadata, $scope.tagKey);
            } else {
              $scope.metadata = formatVals(res.tags, 10);
            }
            $scope.metadataLoaded = true;
          });
        }

        function formatVals(tags, limit, sumLabel) {
          console.log(arguments);
            var formatted = [];
            for (var tag in tags) {
              if (tags.hasOwnProperty(tag) && tags[tag]) {
                formatted.push({x: tag, y: tags[tag]});
              }
            }
            formatted.sort(function(a, b) { return b.y - a.y });
            if (limit) {
              if (sumLabel) {
                var rest = 0;
                for (var i=limit; i<formatted.length; i++) {
                  rest += formatted[i].y;
                }
                formatted = formatted.slice(0, limit - 1);
                if (rest) {
                  console.log(rest);
                  formatted.push({x: sumLabel, y: rest});
                }
              } else {
                formatted = formatted.slice(0, limit);
              }
            }
            return formatted;
        }

        function stripTagKey(axes, tagKey) {
          var prefixLen = tagKey.length + 1;
          for (var i=0; i<axes.length; i++) {
            axes[i].x = axes[i].x.slice(prefixLen);
          }
        }

        $scope.popularChartOpts = {
          chart: {
            type: 'discreteBarChart',
            height: 500,
            showValues: true,
            valueFormat: bytesAbbr,
            duration: 500,
            xAxis: {
              rotateLabels: 60
            },
            yAxis: {
              tickFormat: bytesAbbr
            },
            margin: {
              bottom: 200,
              right: 50
            }
          }
        };

        $scope.breakdownChartOpts = {
          chart: {
            type: 'pieChart',
            height: 500,
            donut: true,
            donutRatio: 0.45,
            showValues: true,
            showLabels: false,
            valueFormat: bytesAbbr,
            duration: 500
          }
        };

        $scope.getTreeData = function(node) {
          var args = {id: $cookies.getObject('awsKey')};
          var nodeId = node ? node.id : '';
          if (nodeId) {
            args.path = nodeId;
          }
          return EstimationModel.getS3SpaceUsageTree(args).$promise.then(function(res) {
            return map(res.dirs, function(size, name) {
              return {
                text: name + ' ' + bytesAbbr(size),
                id: nodeId ? nodeId + '/' + name : name,
                children: true,
                itree: {
                  icon: 'icon-folder'
                }
              };
            });
          });
        };

        function bytesAbbr(bytes) {
          var abbrs = ['B', 'KB', 'MB', 'GB', 'TB'];
          while (bytes / 1000 > 1 && abbrs.length > 1) {
            bytes = bytes / 1000;
            abbrs.shift();
          }
          return bytes.toFixed(2) + ' ' + abbrs[0];
        }

        function map(o, fn) {
          var acc = [];
          for (var key in o) {
            if (o.hasOwnProperty(key)) {
              acc.push(fn(o[key], key));
            }
          }
          return acc;
        }
    }]);
