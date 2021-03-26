var color = d3.scaleOrdinal(d3.schemeSet3);
var simulation, xScale, xAxisG, vis, allNodes, allLinks, allLabels;
var hulls, allHulls;
var ticksize = 100;
var drag = simulation => {

  function dragstarted(d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;

    nodeSelected(this);
  }

  function dragged(d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragended(d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fy = null;
    if(clippingToTimeline) {
      d.fx = d.savedFx;
    } else {
      d.fx = null;
    }
  }

  return d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended);
}

var clippingToTimeline = true;
function clipNodesToTimeline(shouldClip) {
  if(shouldClip) {
    clippingToTimeline = true;
    xAxisG.attr("display", "block");
    simulation.stop();
    allNodes.each(function(d) {
      d.fx = d.savedFx;
    })
    simulation.alpha(1).restart();
  } else {
    clippingToTimeline = false;
    xAxisG.attr("display", "none");
    simulation.stop();
    allNodes.each(function(d) {
      d.fx = null;
    })
    simulation.alpha(1).restart();
  }
}

function createXAxis(scale) {
  return d3.axisBottom(scale)
    .ticks(10)
    .tickFormat(function(d) {
        var yearsAd = ticksize*Math.floor((d/(3600*24*365)+1970)/ticksize);
        if(yearsAd >= 0) {
            return yearsAd + "";
        } else {
            return Math.abs(yearsAd) + " BC"
        }
    });
}

function nodeSelected(node) {
  console.log("nodeSelected", node.id, node.getAttribute("title"), node)
  allNodes.classed("selected", function(n){ return n.id == node.id});
  allLinks.classed("influenced-by", function(l){ return l.target.id == node.id})
  allLinks.classed("influences", function(l){ return l.source.id == node.id})
  allLabels.classed("show", function(n){ return n.id == node.id})
  d3.selectAll(".link.influenced-by").each(function(d, l) {
    d3.select(allNodes._groups[0][d.source.index]).classed("influenced-by", true);
    d3.select(allLabels._groups[0][d.source.index]).classed("show", true);
  });
  d3.selectAll(".link.influences").each(function(d, l) {
    d3.select(allNodes._groups[0][d.target.index]).classed("influences", true);
    d3.select(allLabels._groups[0][d.target.index]).classed("show", true);
  });
}

function resetSelectedNode() {
  allNodes.classed("selected", false);
  allNodes.classed("influenced-by", false);
  allNodes.classed("influences", false);
  allLinks.classed("influences", false);
  allLinks.classed("influenced-by", false);
  allLabels.classed("show", false);
}

function showLabel(node) {
  d3.select('text[id="'+node.id+'"]').classed("show", true);
}

function hideLabel(node) {
  d3.select('text[id="'+node.id+'"]').classed("show", false);
}

function highlightAllSchools(flag) {
  for (var i in schoolgroups){
    highlightSchool(i, flag);
  }
}

function highlightSchool(gid, flag) {
  var n = d3.select('path.hull[id="'+gid+'"]');
  console.log("highlightSchool", schoolgroups[gid].name, hulls[gid].length);
  if (flag) {
    n.attr("display", "visible");
    for (var i = 0; i < hulls[gid].length; i++) {
      d3.selectAll(".node").filter(function(d) { return d.index === hulls[gid][i].index }).style("fill", color(gid));
    }
  } else {
    n.attr("display", "none");
  }
}

function createConvexHull() {
  var groups = [];
  for (var gid in schoolgroups) {
    groups.push({id:gid, name:schoolgroups[gid].name, path:convexHulls(hulls[gid])})
  }
  return groups;
}

function convexHulls(nodes) {
  var offset = 3;
  var hull = [];
  // create point sets
  for (var k=0; k<nodes.length; ++k) {
    var n = nodes[k];
    if (n.size) continue;
    hull.push([n.x-offset, n.y-offset]);
    hull.push([n.x-offset, n.y+offset]);
    hull.push([n.x+offset, n.y-offset]);
    hull.push([n.x+offset, n.y+offset]);
  }
  // create convex hull
  return d3.polygonHull(hull);
}

function drawCluster(d) {
  if (isNaN(d.path[0][0])) return "";
  var curve = d3.line().curve(d3.curveCardinalClosed.tension(0.8));
  return curve(d.path);
}

function nodeRadius(score) {
  return Math.sqrt(score * 2500 * 3.14)
}

function groupSimilarity(a, b) {
  // console.log("groupSimilarity", a, b, node_info[a], node_info[b])
  var n1 = node_info[a].school.split(","),
      n2 = node_info[b].school.split(",");
  var set1 = n1[0]==""?new Set():new Set(n1),
      set2 = n2[0]==""?new Set():new Set(n2);
  let intersect= new Set([...set1].filter(i => set2.has(i)));
  return intersect.size;
}

class ThinkersNet {

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
      .call(d3.zoom().on("zoom", this.redraw));
    this.rect = this.outer.append("rect")
      .attr("class", "background")
      .attr("width", "100%")
      .attr("height", "100%");
    vis = this.outer.append("g");
    this.defs = this.outer.append("defs")
  }

  redraw() {
    vis.attr('transform', d3.event.transform);
    var newXScale = d3.event.transform.rescaleX(xScale);
    xAxisG.call(createXAxis(newXScale))
  }

  initGraph(){
    this.hullg = vis.append("g");
    this.linkg = vis.append("g");
    this.nodeg = vis.append("g");
  }

  clearGraph() {
    this.outer.selectAll(".link").remove();
    this.outer.selectAll(".node").remove();
    this.outer.selectAll(".nlabel").remove();
    this.outer.selectAll(".elabel").remove();
    this.outer.selectAll(".hull").remove();
  }

  drawHull(hid, path) {
    this.hullg.append("path")
      .attr("class", "hull")
      .attr("d", path)
      .style("fill", color(hid));
  }

  drawGraph() {
    const min_radius = 1;
    const xScale_margin = 80;

    const timestamps = viewgraph.nodes.map(d => d.born);
    const timerange = d3.extent(timestamps)
    var yearrange = (timerange[1]-timerange[0])/(3600*24*60);
    if (yearrange < 2000) ticksize = 5;

    // add Y axis
    xScale = d3.scaleLinear()
      .domain(timerange).nice()
      .range([xScale_margin, this.width - xScale_margin]);
    xAxisG = this.outer.append("g")
      .classed('x-axis', true)
      .call(createXAxis(xScale))
      .attr("display", "block")
      .attr("transform", "translate(" + 0 + "," + (this.height - 30) + ")");

    for (var i = 0; i < viewgraph.nodes.length; i++) {
      viewgraph.nodes[i].savedFx = xScale(viewgraph.nodes[i].born);
      viewgraph.nodes[i].fx = xScale(viewgraph.nodes[i].born);
    }

    const links = viewgraph.links.map(d => Object.create(d));
    const nodes = viewgraph.nodes.map(d => Object.create(d));

    // draw force directed network
    simulation = d3.forceSimulation(nodes).alpha(0.3)
      .force("link", d3.forceLink(links).id(d => d.id)
        .distance(function(l, i) {
          // return 200;
          return 200/(1+10*groupSimilarity(l.source.index, l.target.index));
          // shorter edge length if source and target have a high group similarity
        })
        .strength(function(l, i) {
          return 0.5;
        }))
      .force("collide", d3.forceCollide().radius(d => nodeRadius(d.score)+1).iterations(2))
      .force("charge", d3.forceManyBody())
      .force("center", d3.forceCenter(this.width / 2, this.height / 2))
      .force("x", d3.forceX(1))
      .force("y", d3.forceY(1));

    allLinks = this.linkg.selectAll(".link")
      .data(links)
      .enter().append("line")
      .attr("id", d => d.source.index + "_" + d.target.index)
      .attr("class", "link");

    allNodes = this.nodeg.selectAll(".node")
      .data(nodes)
      .enter().append("circle")
      .attr("id", d => d.id)
      .attr("title", d => d.name)
      .attr("data_pcount", d => d.pcount)
      .attr("data_ccount", d => d.ccount)
      .attr("data_authorid", d => d.authorid)
      .attr("data_school", d => d.school)
      .attr("class", "node")
      .attr("savedFx", d => xScale(d.born))
      .attr("r", d => nodeRadius(d.centrality))
      .on("click", function() {
        nodeSelected(this);
      })
      .on("mouseover", function() {
        nodeSelected(this);
      })
      .on("mouseout", function() {
        resetSelectedNode();
      })
      .call(drag(simulation));

    hulls = {};
    for (var gid in schoolgroups) {
      var selectedNodes = [];
      for (var i = 0; i < schoolgroups[gid].list.length; i++) {
        var n = d3.select('circle[id="'+schoolgroups[gid].list[i]+'"]');
        selectedNodes.push(n.datum());
      }
      hulls[gid] = selectedNodes;
    }

    allHulls = this.hullg.selectAll("path.hull")
      .data(createConvexHull())
    .enter().append("path")
      .attr("class", "hull")
      .attr("id", d => d.id)
      .attr("d", drawCluster)
      .attr("display", "none")
      .style("fill", d => color(d.id));

    allLabels = this.nodeg.selectAll(".label")
      .data(nodes)
      .enter().append("text")
      .attr("id", d => d.id)
      .attr("class", "label")
      .text(d => d.name);

    simulation.on("tick", () => {
      allLinks
          .attr("x1", d => d.source.x)
          .attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x)
          .attr("y2", d => d.target.y);

      allNodes
          .attr("cx", d => d.x)
          .attr("cy", d => d.y);
      allLabels
          .attr("x", d => d.x+3)
          .attr("y", d => d.y+3);
      allHulls.data(createConvexHull())
          .attr("d", drawCluster);
    });

    this.rect.on("click", function() {
      resetSelectedNode();
    })

  }

}
