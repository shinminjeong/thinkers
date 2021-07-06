var color = d3.scaleOrdinal(d3.schemeSet3);
var simulation, xScale, xSeq, vis, allNodes, allLinks, allLabels;
var sortedNodes = [], xAxisG = [];
var yPos = 250, seqH = 25;

function getYear(time) {
  return Math.floor(time/(3600*24*365))+1970;
}
function getTime(year) {
  return (year-1970)*(3600*24*365);
}

// linear timeAxis for publication/citation chart
function tickScale(d) {
  var yearsAd = getYear(d);
  if(yearsAd >= 0) {
      return yearsAd + "";
  } else {
      return Math.abs(yearsAd) + " BC"
  }
}
function createXAxis(scale) {
  return d3.axisBottom(scale)
    .tickFormat(tickScale);
}

// non-linear timeAxis generated from node sequence
function tickScaleSeq(d) {
  if (sortedNodes[d] == undefined) return "";
  var yearsAd = getYear(sortedNodes[d].born);
  if (sortedNodes[d].yearGap < 2) return "";
  if(yearsAd >= 0) {
      return yearsAd + "";
  } else {
      return Math.abs(yearsAd) + " BC"
  }
}
function createXAxisSeq(scale) {
  return d3.axisTop(scale)
    .ticks(sortedNodes.length)
    .tickFormat(tickScaleSeq);
}


function updateGraph(newXScale) {
  simulation.stop();
  d3.selectAll(".bar-pub").each(function(d) {
    d3.select(this)
      .attr("x", newXScale(getTime(d.year)))
      .attr("width", tickWidth(newXScale));
  });
  d3.selectAll(".cit-pub").each(function(d) {
    d3.select(this)
      .attr("x", newXScale(getTime(d.year)))
      .attr("width", tickWidth(newXScale));
  });

  allNodes.each(function(d, i) {
    d.fx = newXScale(d.born);
  });
  simulation.alpha(1).restart();
}

function nodeClicked(node) {
  console.log("nodeClicked", node.id, node.getAttribute("title"), node);
  var paperg = vis.append("g");

  // ego
  console.log(ego_node);
  console.log(charts.pub_chart);
  paperg.append("rect")
    .attr("x", xScale(ego_node.born))
    .attr("y", yPos+seqH*1.3-3)
    .attr("width", xScale(getTime(80))-xScale(getTime(0)))
    .attr("height", 6)
    .attr("fill", "#ddd");
  for (var i in charts.pub_chart) {
    paperg.append("circle")
      .attr("cx", xScale(getTime(charts.pub_chart[i].year)))
      .attr("cy", yPos+seqH*1.3)
      .attr("fill", "#ddd")
      .attr("opacity", 0.5)
      .attr("r", charts.pub_chart[i].value);
  }

  // selected alter
  papers = node.getAttribute("data_inftimes").split(",");
  paperg.append("rect")
    .attr("x", xScale(+papers[0]-20*(3600*24*365)))
    .attr("y", yPos+seqH*1.7-3)
    .attr("width", xScale(getTime(80))-xScale(getTime(0)))
    .attr("height", 6)
    .attr("fill", "#ddd");

  for (var i in papers) {
    paperg.append("circle")
      .attr("cx", xScale(+papers[i]))
      .attr("cy", yPos+seqH*1.7)
      .attr("fill", "#ddd")
      .attr("opacity", 0.5)
      .attr("r", Math.random()*10*Math.random());
  }


}

function nodeSelected(node) {
  console.log("nodeSelected", node.id, node.getAttribute("title"), node)
  allNodes.classed("selected", function(n){ return n.id == node.id});
  allNodes.classed("unselected", function(n){ return n.id != node.id});
  allLinks.classed("influenced-by", function(l){ return l.target.id == node.id})
  allLinks.classed("influences", function(l){ return l.source.id == node.id})
  allLinks.classed("unselected", function(l){ return l.source.id != node.id || l.target.id != node.id})
  // allLabels.classed("show", function(n){ return n.id == node.id})
  d3.selectAll(".wlink.influenced-by").each(function(d, l) {
    d3.select(allNodes._groups[0][d.source.index]).classed("influenced-by", true);
    d3.select(allLabels._groups[0][d.source.index]).classed("show", true);
  });
  d3.selectAll(".wlink.influences").each(function(d, l) {
    d3.select(allNodes._groups[0][d.target.index]).classed("influences", true);
    d3.select(allLabels._groups[0][d.target.index]).classed("show", true);
  });
}

function resetSelectedNode() {
  allNodes.classed("selected", false);
  allNodes.classed("unselected", false);
  allNodes.classed("influenced-by", false);
  allNodes.classed("influences", false);
  allLinks.classed("influences", false);
  allLinks.classed("influenced-by", false);
  allLinks.classed("unselected", false);
  allLabels.classed("show", function(d) {
    if (d.id === ego_node.pageid || nodeRadiusWiki(d.centrality) > 100) return true;
    else return false;
  })
}

function showLabel(node) {
  d3.select('text[id="'+node.id+'"]').classed("show", true);
}

function hideLabel(node) {
  d3.select('text[id="'+node.id+'"]').classed("show", false);
}

function nodeRadiusWiki(score) {
  return Math.sqrt(score * 5000 * 3.14)
}

function linkArc(d) {
  var sx = d.source.x, sy = d.source.y,
      tx = d.target.x, ty = d.target.y;
  var dx = tx-sx, dy = ty-sy,
      dr = Math.sqrt(dx * dx + dy * dy);

  return "M" + sx + "," + sy + "A" + dr + "," + dr + " 0 0,0 " + tx + "," + ty;
}

function tickWidth(scale) {
    return scale(getTime(1971)) - scale(getTime(1970));
}


class ThinkersEgoNet {

  constructor(div_id, w, h) {
    this.div_id = div_id;
    this.width = w;
    this.height = h;
    this.setContainer(div_id);
  }

  setContainer(div_id) {
    this.outer = d3.select(div_id).append("svg")
      .attr("width", this.width)
      .attr("height", this.height)
      .attr("pointer-events", "all")
      .call(d3.zoom().scaleExtent([1, 10]).on("zoom", this.redraw));
    this.rect = this.outer.append("rect")
      .attr("fill", "transparent")
      .attr("width", "100%")
      .attr("height", "100%");
    vis = this.outer.append("g");
    this.defs = this.outer.append("defs")
  }

  redraw() {
    var newXScale = d3.event.transform.rescaleX(xScale);
    for (var i = 0; i < 3; i++) xAxisG[i].call(createXAxis(newXScale));
    updateGraph(newXScale);
  }

  initGraph(){
    this.barg = vis.append("g");
    this.gridg = vis.append("g");
    this.linkg = vis.append("g");
    this.nodeg = vis.append("g");
    this.timelineg = vis.append("g");
  }

  clearGraph() {
    this.outer.selectAll(".link").remove();
    this.outer.selectAll(".node").remove();
    this.outer.selectAll(".nlabel").remove();
  }

  drawPubCiteChart() {
    console.log(ego_node)
    var pubMaxYear = d3.max(viewgraph.pub_data, function(d) { return d.year+1; });
    var citMaxYear = d3.max(viewgraph.cite_data, function(d) { return d.year+1; });
    const timerange = d3.extent([ego_node.born, Math.max(getTime(pubMaxYear), getTime(citMaxYear))]);
    const chartRightMargin = 100, chartYPos = 110;
    var icon_size = 24, pub_height = 80, cite_height = 80;

    // add X axis
    xScale = d3.scaleLinear()
      .domain(timerange)
      .range([this.width/2, this.width - chartRightMargin]);
    var xAx = this.outer.append("g")
      .classed('x-axis', true)
      .call(createXAxis(xScale))
      .attr("display", "block")
      .attr("transform", "translate(" + 0 + "," + chartYPos + ")");

    // draw publication and citation chart
    var pub_y = d3.scaleLinear()
      .domain([0, d3.max(viewgraph.pub_data, function(d) { return d.value+1; })])
      .range([pub_height, 0]);
    var cit_y = d3.scaleLinear()
      .domain([0, d3.max(viewgraph.cite_data, function(d) { return d.value+1; })])
      .range([cite_height, 0]);

    this.barg.append("image")
      .attr("xlink:href", "static/images/user-icon.svg")
      .attr("x", this.width/2-icon_size/2)
      .attr("y", chartYPos-icon_size+1)
      .attr("width", icon_size)
      .attr("height", icon_size);

    this.barg.selectAll(".bar-pub")
      .data(viewgraph.pub_data)
      .enter().append("rect")
        .attr("class", "bar-pub")
        .attr("id", d => d.year)
        .attr("x", d => xScale(getTime(d.year)))
        .attr("y", d => chartYPos-pub_height+pub_y(d.value))
        .attr("width", tickWidth(xScale))
        .attr("height", d => pub_height-pub_y(d.value))
        .style("fill", "#6bacd0")
        .style("cursor", "pointer");
    this.barg.selectAll(".cit-pub")
      .data(viewgraph.cite_data)
      .enter().append("rect")
        .attr("class", "cit-pub")
        .attr("id", d => d.year)
        .attr("x", d => xScale(getTime(d.year)))
        .attr("y", chartYPos)
        .attr("width", tickWidth(xScale))
        .attr("height", d => cite_height-cit_y(d.value))
        .style("fill", "#e48268")
        .style("cursor", "pointer");
  }

  drawGraph(ego_node) {
    const min_radius = 1;
    const xScale_margin = 80;

    var egoids = [
      ego_node.pageid+"_pub",
      ego_node.pageid,
      ego_node.pageid+"_mag",
    ]

    this.drawPubCiteChart();

    var totalYears = viewgraph.nodes.map(d => d.born);
    sortedNodes = viewgraph.nodes.sort(function(a, b){ return a.born-b.born; });
    xSeq = d3.scaleLinear()
      .domain([0, sortedNodes.length-1])
      .range([xScale_margin, this.width - xScale_margin]);

    // draw non-linear grid
    var tickW = xSeq(1)-xSeq(0);
    for (var i = sortedNodes.length-1; i > 0; i--) {
      var numYears = getYear(sortedNodes[i].born)-getYear(sortedNodes[i-1].born);
      sortedNodes[i].yearGap = numYears;
      for (var j = 0; j < numYears; j++) {
        var pos = xScale_margin + i*tickW - j*tickW/numYears;
        this.gridg.append("line")
          .attr("class", "grid")
          .attr("x1", pos)
          .attr("x2", pos)
          .attr("y1", yPos-seqH)
          .attr("y2", yPos+seqH*sortedNodes.length)
      }
    }
    // draw the first line
    this.gridg.append("line")
      .attr("class", "grid")
      .attr("x1", xScale_margin)
      .attr("x2", xScale_margin)
      .attr("y1", yPos-seqH)
      .attr("y2", yPos+seqH*sortedNodes.length)

    // draw non-linear time-axis
    var xAxSeq = this.outer.append("g")
      .classed('x-axis', true)
      .call(createXAxisSeq(xSeq))
      .attr("display", "block")
      .attr("transform", "translate(" + 0 + "," + (yPos-seqH) + ")");


    const nodes = [], links = [];
    // author nodes
    for (var i = 0; i < sortedNodes.length; i++) {
      sortedNodes[i].savedFx = xSeq(i);
      sortedNodes[i].fx = xSeq(i);
      sortedNodes[i].fy = yPos+i*seqH;
      nodes.push(sortedNodes[i]);
    }


    // WIKI edges
    for (var i = 0; i < viewgraph.links.length; i++) {
      var d = viewgraph.links[i];
      if (egoids.includes(d.source) || egoids.includes(d.target)) // filter only direct edges
        links.push(Object.create(d));
    }
    // MAG edges
    // for (var i = 0; i < viewgraph.links_f.length; i++) {
    //   var d = viewgraph.links_f[i];
    //   d.type = "f";
    //   links.push(Object.create(d));
    // }

    this.defs.selectAll("marker")
      .data(links)
      .enter().append("marker")
      .attr("id", "arrow")
      .attr("viewBox", "0 0 20 20")
      .attr("refX", 30)
      .attr("refY", 10)
      .attr("markerWidth", 20)
      .attr("markerHeight", 20)
      .attr("markerUnits", "strokeWidth")
      .attr("orient", "auto-start-reverse")
    .append("path")
      .attr("d", "M0,0L0,20L20,10")
      .style("fill", "#ccc");


    // draw force directed network
    simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id));

    allLinks = this.linkg.selectAll(".wlink")
      .data(links)
      .enter().append("path")
      .attr("id", d => d.source.index + "_" + d.target.index)
      .attr("class", function(d) {
        if (d.type === "w") {
          return "wlink";
        } else { // MAG edges
          return "wlink";
        }
      })
      .attr("stroke-width", d => d.value/2)
      .attr("marker-start", "url(#arrow)");

    allNodes = this.nodeg.selectAll(".wnode")
      .data(nodes)
      .enter().append("circle")
      .attr("id", d => d.id)
      .attr("title", d => d.name)
      .attr("data_authorid", d => d.authorid)
      .attr("data_pubtimes", d => d.pubtimes)
      .attr("data_inftimes", d => d.inftimes)
      .attr("class", function(d) {
        if (d.type === "paper") return "wnode paper";
        else if (egoids.includes(d.id))  return "wnode egonode";
        else return "wnode";
      })
      .attr("r", function(d) {
        if (egoids.includes(d.id)) return 10;
        else return nodeRadiusWiki(d.r);
      })
      .on("click", function() {
        nodeClicked(this);
      })
      .on("mouseover", function() {
        showLabel(this);
        nodeSelected(this);
      })
      .on("mouseout", function() {
        // hideLabel(this);
        resetSelectedNode();
      });

    allLabels = this.nodeg.selectAll(".wlabel")
      .data(nodes)
      .enter().append("text")
      .attr("id", d => d.id)
      .attr("class", function(d) {
        return "wlabel";
      })
      .text(d => d.name);

    simulation.on("tick", () => {
      allNodes
          .attr("cx", d => d.x)
          .attr("cy", d => d.y);
      allLabels
          .attr("x", d => d.x+8)
          .attr("y", function(d) {
            return d.y+15;
          })
      allLinks
          .attr("d", function(d) {
            return linkArc(d);
          })
    });

    this.rect.on("click", function() {
      resetSelectedNode();
    })

  }

}
