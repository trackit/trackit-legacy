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
    .translate([(width / 2), (height / 2)])
    .precision(.1);

  geoPath = d3.geo.path()
    .projection(projection);



  g.selectAll('path').attr('d', geoPath);

  markers.attr("transform", function(d) {
    return "translate(" + projection([d.location.long, d.location.lat]) + ")";
  });

  donuts.attr('d', arc.innerRadius(getMarkersRadius() - donutWidth).outerRadius(getMarkersRadius()));
  circle.attr('r', getMarkersRadius());

}


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
  .translate([(width / 2), (height / 2)])
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
  var min = 55; //min marker radius
  var max = 70; // max marker radius
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



var markers = svg.selectAll(".mark")
  .data(marksData)
  .enter()
  .append("g")
  .attr('class', 'mark')
  .attr("transform", function(d) {
    return "translate(" + projection([d.location.long, d.location.lat]) + ")";
  }).on("mouseover", function(d) {
    var parent = d3.transform(d3.select(this).attr("transform")).translate;
    tooltip.style("top", parent[1] + 80 + 'px').style("left", parent[0] - 60 + 'px');


    if (d.tests[3].count > 0)
      tooltipHealth.html('<div class="row"><div class="col-xs-3"><i class="fa fa-exclamation-triangle fa-4x red"></i></div><div class="col-xs-9"> <p>Some of your volumes snapshots are more than 30 days old</p></div></div>');
    else if (d.tests[2].count > 0) {
      tooltipHealth.html('<div class="row"><div class="col-xs-3"><i class="fa fa-exclamation-circle fa-4x orange"></i></div><div class="col-xs-9"> <p>The most recent of your volumes snapshots is between 7 and 30 days old.</p></div></div>');
    } else {
      tooltipHealth.html('<div class="row"><div class="col-xs-3"><i class="fa fa-check fa-4x green"></i></div><div class="col-xs-9"> <p>Your instances are backed-up.</p></div></div>');
    }

    tooltipChart.selectAll("rect")
      .data(d.tests)
      .enter()
      .append("rect")
      .attr("x", function(d, i) {
        return i * (tooltipChartWidth / 4) + 3;
      })
      .attr("y", function(d) {
        var max = getMaxCount(d3.select(this.parentNode).selectAll('rect').data());
        return tooltipChartHeight - ((d.count * 100) / max) + tooltipChartHeightMargin;
      }).attr("width", (tooltipChartWidth / 4) - 3)
      .attr("height", function(d) {
        var max = getMaxCount(d3.select(this.parentNode).selectAll('rect').data());
        return ((d.count * 100) / max);
      })
      .attr('fill', function(d, i) {
        return color(d.label);
      });

    tooltipChart.selectAll("text")
      .data(d.tests)
      .enter()
      .append("text")
      .text(function(d) {
        if (d.count)
          return d.count;
      })
      .attr("text-anchor", "middle")
      .attr("class", "montsbold")
      .attr("font-size", "13px")
      .attr("fill", "black")
      .attr("x", function(d, i) {
        return i * (tooltipChartWidth / 4) + (tooltipChartWidth / 4) / 2;
      })
      .attr("y", function(d) {
        var max = getMaxCount(d3.select(this.parentNode).selectAll('rect').data());
        return tooltipChartHeight - ((d.count * 100) / max) + tooltipChartHeightMargin - 7;
      });


    tooltip.transition()
      .duration(400)
      .style("opacity", .95);

  })
  .on("mouseout", function(d) {
    tooltip.transition()
      .duration(200)
      .style("opacity", 0);
    tooltipHealth.html('');
    tooltipChart.selectAll('rect').remove();
    tooltipChart.selectAll("text").remove();

  });

var circle = markers.append('circle')
  .attr('r', getMarkersRadius())
  .attr('fill', 'rgba(255, 255, 255, 0.80)');






var markText = markers.append('g');

markText.append('text')
  .attr("text-anchor", "middle")
  .attr('y', 5)
  .classed("montslight", true)
  .classed("map-risks-total", true)
  .text(function(d) {
    return getTotalRisks(d);
  });

markText.append('text')
  .attr('y', 30)
  .attr("text-anchor", "middle")
  .text(function(d) {
    return d.name
  });

var donuts = markers.selectAll(".donuts")
  .data(function(d) {
    return pie(d.tests);
  })
  .enter()
  .append('path')
  .attr('class', 'donuts')
  .attr('d', arc.innerRadius(getMarkersRadius() - donutWidth).outerRadius(getMarkersRadius()))
  .attr('fill', function(d, i) {
    return color(d.data.label);
  });

var tooltip = d3.selectAll('.world-map')
  .append('div')
  .attr('class', 'world-map-tooltip')
  .style('opacity', 0);

var tooltipHealth = tooltip.append('div')
  .attr('class', 'tooltip-health');

var tooltipChart = tooltip.append("svg")
  .attr("width", tooltipChartWidth)
  .attr("height", tooltipChartHeight + tooltipChartHeightMargin);
