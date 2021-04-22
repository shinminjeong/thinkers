var color = d3.scaleOrdinal(d3.schemeSet3);
var simulation, yScale, yAxisG, vis, allNodes, allLinks, allLabels;
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
    d.fx = d.savedFx;
    if(clippingToTimeline) {
      d.fy = d.savedFy;
    } else {
      d.fy = null;
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
    yAxisG.attr("display", "block");
    simulation.stop();
    allNodes.each(function(d) {
      d.fy = d.savedFy;
    })
    simulation.alpha(1).restart();
  } else {
    clippingToTimeline = false;
    yAxisG.attr("display", "none");
    simulation.stop();
    allNodes.each(function(d) {
      d.fy = null;
    })
    simulation.alpha(1).restart();
  }
}

function getYear(time) {
  return time/(3600*24*365)+1970;
}

function createYAxis(scale) {
  return d3.axisLeft(scale)
    .ticks(10)
    .tickFormat(function(d) {
        var yearsAd = ticksize*Math.floor(getYear(d)/ticksize);
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
  allNodes.classed("unselected", function(n){ return n.id != node.id});
  allLinks.classed("influenced-by", function(l){ return l.target.id == node.id})
  allLinks.classed("influences", function(l){ return l.source.id == node.id})
  allLinks.classed("unselected", function(l){ return l.source.id != node.id || l.target.id != node.id})
  allLabels.classed("show", function(n){ return n.id == node.id})
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
    if (d.id === ego_node || nodeRadiusWiki(d.r) > 5) return true;
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

function wikiLinkArc(d) {
  var sx = d.source.x, sy = d.source.y,
      tx = d.target.x, ty = d.target.y;
  var dx = tx-sx, dy = ty-sy,
      dr = Math.sqrt(dx * dx + dy * dy)*2;
  return "M" + sx + "," + sy + "A" + dr + "," + dr + " 0 0,1 " + tx + "," + ty;
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
      .call(d3.zoom().on("zoom", this.redraw));
    vis = this.outer.append("g");
    this.defs = this.outer.append("defs")
  }

  redraw() {
    vis.attr('transform', d3.event.transform);
    var newYScale = d3.event.transform.rescaleY(yScale);
    yAxisG.call(createYAxis(newYScale))
  }

  initGraph(){
    this.linkg = vis.append("g");
    this.nodeg = vis.append("g");
  }

  clearGraph() {
    this.outer.selectAll(".link").remove();
    this.outer.selectAll(".node").remove();
    this.outer.selectAll(".nlabel").remove();
    this.outer.selectAll(".elabel").remove();
  }

  drawGraph(ego_node) {
    const min_radius = 1;
    const yScale_margin = 80;

    const timestamps = viewgraph.nodes.map(d => d.born);
    const timerange = d3.extent(timestamps)
    var yearrange = (timerange[1]-timerange[0])/(3600*24*60);
    if (yearrange < 2000) ticksize = 5;

    // add Y axis
    yScale = d3.scaleLog()
      .domain(timerange)
      .range([yScale_margin, this.height - yScale_margin]);
    yAxisG = this.outer.append("g")
      .classed('y-axis', true)
      .call(createYAxis(yScale))
      .attr("display", "block")
      .attr("transform", "translate(" + 50 + "," + 0 + ")");

    for (var i = 0; i < viewgraph.nodes.length; i++) {
      viewgraph.nodes[i].savedFy = yScale(viewgraph.nodes[i].born);
      viewgraph.nodes[i].fy = yScale(viewgraph.nodes[i].born);
    }

    const links = viewgraph.links.map(d => Object.create(d));
    const nodes = viewgraph.nodes.map(d => Object.create(d));

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
    simulation = d3.forceSimulation(nodes).alpha(0.3)
      .force("link", d3.forceLink(links).id(d => d.id)
        .distance(function(l, i) {
          return 200;
        })
        .strength(function(l, i) {
          return 0.5;
        }))
      .force("collide", d3.forceCollide().radius(d => nodeRadiusWiki(d.score)+1).iterations(2))
      .force("charge", d3.forceManyBody())
      .force("center", d3.forceCenter(this.width / 2, this.height / 2))
      .force("x", d3.forceX(1))
      .force("y", d3.forceY(1));

    allLinks = this.linkg.selectAll(".wlink")
      .data(links)
      .enter().append("path")
      .attr("id", d => d.source.index + "_" + d.target.index)
      .attr("class", "wlink")
      // .attr("marker-start", "url(#arrow)");

    allNodes = this.nodeg.selectAll(".wnode")
      .data(nodes)
      .enter().append("circle")
      .attr("id", d => d.id)
      .attr("title", d => d.name)
      .attr("data_authorid", d => d.authorid)
      .attr("class", function(d) {
        if (d.id === ego_node) return "wnode egonode"
        else if (getYear(d.born) < 1750) return "wnode old";
        else return "wnode";
      })
      .attr("savedFx", this.width/2)
      .attr("savedFy", d => yScale(d.born))
      .attr("r", d => nodeRadiusWiki(d.r))
      .on("click", function() {
        nodeSelected(this);
      })
      .on("mouseover", function() {
        showLabel(this);
        nodeSelected(this);
      })
      .on("mouseout", function() {
        hideLabel(this);
        resetSelectedNode();
      })
      .call(drag(simulation));

    allLabels = this.nodeg.selectAll(".wlabel")
      .data(nodes)
      .enter().append("text")
      .attr("id", d => d.id)
      .attr("class", function(d) {
        if (d.id === ego_node) return "wlabel egonode show";
        else if (nodeRadiusWiki(d.r) > 5) return "wlabel show";
        else return "wlabel";
      })
      .text(d => d.name);

    simulation.on("tick", () => {
      allNodes
          .attr("cx", d => d.x)
          .attr("cy", d => d.y);
      allLabels
          .attr("x", d => d.x+5)
          .attr("y", d => d.y+5);
      allLinks
          .attr("d", d=> wikiLinkArc(d))
    });

  }

}
