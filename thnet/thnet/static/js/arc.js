var color = d3.scaleOrdinal(d3.schemeSet3);
var simulation, xScale, xAxisG, vis, allNodes, allLinks, allLabels;
var ticksize = 10, yPos = 400;

function getYear(time) {
  return time/(3600*24*365)+1970;
}

function getTime(year) {
  return (year-1970)*(3600*24*365);
}

function createXAxis(scale) {
  return d3.axisBottom(scale)
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

function updateGraph(newXScale) {
  simulation.stop();
  allNodes.each(function(d, i) {
    d.fx = newXScale(viewgraph.nodes[i].born);
  });
  simulation.alpha(1).restart();
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
    if (d.id === ego_node || nodeRadiusWiki(d.centrality) > 100) return true;
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
      dr = dx/2;
  return "M" + sx + "," + sy + "A" + dr + "," + dr + " 0 0,0 " + tx + "," + ty;
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
      .attr("fill", "white")
      .attr("width", "100%")
      .attr("height", "100%");
    vis = this.outer.append("g");
    this.defs = this.outer.append("defs")
  }

  redraw() {
    var newXScale = d3.event.transform.rescaleX(xScale);
    xAxisG.call(createXAxis(newXScale));
    updateGraph(newXScale);
  }

  initGraph(){
    this.linkg = vis.append("g");
    this.nodeg = vis.append("g");
  }

  clearGraph() {
    this.outer.selectAll(".link").remove();
    this.outer.selectAll(".node").remove();
    this.outer.selectAll(".nlabel").remove();
  }

  drawGraph(ego_node) {
    const min_radius = 1;
    const xScale_margin = 80;

    const timestamps = viewgraph.nodes.map(d => d.born);
    const timerange = d3.extent(timestamps);

    // add X axis
    xScale = d3.scaleLog()
      .domain(timerange)
      .range([xScale_margin, this.width - xScale_margin]);
    xAxisG = this.outer.append("g")
      .classed('x-axis', true)
      .call(createXAxis(xScale))
      .attr("display", "block")
      .attr("transform", "translate(" + 50 + "," + yPos + ")");

    for (var i = 0; i < viewgraph.nodes.length; i++) {
      viewgraph.nodes[i].savedFx = xScale(viewgraph.nodes[i].born);
      viewgraph.nodes[i].fx = xScale(viewgraph.nodes[i].born);
      viewgraph.nodes[i].fy = yPos;
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
    simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id));

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
      .attr("r", d => nodeRadiusWiki(d.centrality))
      .on("click", function() {
        nodeSelected(this);
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
        if (d.id === ego_node) return "wlabel egonode show";
        else if (nodeRadiusWiki(d.centrality) > 100) return "wlabel show";
        else return "wlabel";
      })
      .text(d => d.name);

    simulation.on("tick", () => {
      allNodes
          .attr("cx", d => d.x)
          .attr("cy", d => d.y);
      allLabels
          .attr("x", d => d.x+5)
          .attr("y", d => d.y+5)
          .attr("transform", d => "rotate(90,"+(d.x-10)+","+(yPos+10)+")");
      allLinks
          .attr("d", d=> wikiLinkArc(d))
    });

    this.rect.on("click", function() {
      resetSelectedNode();
    })

  }

}
