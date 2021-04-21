var color = d3.scaleOrdinal(d3.schemeSet3);
var simulation, xScale, xAxisG_1, xAxisG_2, vis, allNodes, allLinks, allLabels;
var ticksize = 10, yPos = 400, egoH = 15;

function getYear(time) {
  return time/(3600*24*365)+1970;
}

function getTime(year) {
  return (year-1970)*(3600*24*365);
}

function tickScale(d) {
  var yearsAd = ticksize*Math.floor(getYear(d)/ticksize);
  if(yearsAd >= 0) {
      return yearsAd + "";
  } else {
      return Math.abs(yearsAd) + " BC"
  }
}

function createXAxisTop(scale) {
  return d3.axisTop(scale)
    .ticks(10)
    .tickFormat(tickScale);
}
function createXAxisBottom(scale) {
  return d3.axisBottom(scale)
    .ticks(10)
    .tickFormat(tickScale);
}

function updateGraph(newXScale) {
  simulation.stop();
  allNodes.each(function(d, i) {
    d.fx = newXScale(d.born);
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

  if (d.type === "w") { // wiki edges
    if (dx > 0) // to draw upper arc for wiki edges
      return "M" + sx + "," + sy + "A" + dr + "," + dr + " 0 0,1 " + tx + "," + ty;
    else return "M" + sx + "," + sy + "A" + dr + "," + dr + " 0 0,0 " + tx + "," + ty;
  } else { // mag edges
    if (d.direction == "influencing")
      return "M" + sx + "," + sy + "A" + dr + "," + dr + " 0 0,0 " + tx + "," + ty;
    else return "M" + sx + "," + sy + "A" + dr + "," + dr + " 0 0,1 " + tx + "," + ty;
  }
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
    xAxisG_1.call(createXAxisTop(newXScale));
    xAxisG_2.call(createXAxisBottom(newXScale));
    updateGraph(newXScale);
  }

  initGraph(){
    this.linkg = vis.append("g");
    this.nodeg = vis.append("g");
    this.egog = vis.append("g");
  }

  clearGraph() {
    this.outer.selectAll(".link").remove();
    this.outer.selectAll(".node").remove();
    this.outer.selectAll(".nlabel").remove();
  }

  drawGraph(ego_node) {
    const min_radius = 1;
    const xScale_margin = 80;

    const timestamps_w = viewgraph.nodes_w.map(d => d.born);
    const timestamps_f = viewgraph.nodes_f.map(d => d.born);
    const tr_w = d3.extent(timestamps_w),
          tr_f = d3.extent(timestamps_f);
    const timerange = [Math.min(tr_w[0], tr_f[0]), Math.max(tr_w[1], tr_f[1])];

    // add X axis
    xScale = d3.scaleLinear()
      .domain(timerange).nice()
      .range([xScale_margin, this.width - xScale_margin]);
    xAxisG_1 = this.outer.append("g")
      .classed('x-axis', true)
      .call(createXAxisTop(xScale))
      .attr("display", "block")
      .attr("transform", "translate(" + 0 + "," + (yPos-egoH) + ")");
    xAxisG_2 = this.outer.append("g")
      .classed('x-axis', true)
      .call(createXAxisBottom(xScale))
      .attr("display", "block")
      .attr("transform", "translate(" + 0 + "," + (yPos+egoH) + ")");

    // // draw egobar
    // this.egog.selectAll(".wnode")
    //   .data(viewgraph.ego_timeline)
    //   .enter().append("circle")
    //   .attr("cx", d => xScale(d.year))
    //   .attr("cy", yPos)
    //   .attr("r", d => d.count);


    const nodes = [], links = [];
    // WIKI nodes
    for (var i = 0; i < viewgraph.nodes_w.length; i++) {
      viewgraph.nodes_w[i].savedFx = xScale(viewgraph.nodes_w[i].born);
      viewgraph.nodes_w[i].fx = xScale(viewgraph.nodes_w[i].born);
      viewgraph.nodes_w[i].fy = yPos-egoH;
      viewgraph.nodes_w[i].type = "w";
      nodes.push(viewgraph.nodes_w[i]);
    }
    // MAG nodes
    for (var i = 0; i < viewgraph.nodes_f.length; i++) {
      viewgraph.nodes_f[i].savedFx = xScale(viewgraph.nodes_f[i].born);
      viewgraph.nodes_f[i].fx = xScale(viewgraph.nodes_f[i].born);
      if (viewgraph.nodes_f[i].node === "ego")
        viewgraph.nodes_f[i].fy = yPos;
      else
        viewgraph.nodes_f[i].fy = yPos+egoH+20*(viewgraph.nodes_f[i].index);
      viewgraph.nodes_f[i].type = "f";
      nodes.push(viewgraph.nodes_f[i]);
    }

    // WIKI edges
    for (var i = 0; i < viewgraph.links_w.length; i++) {
      var d = viewgraph.links_w[i];
      d.type = "w";
      if (d.source === ego_node || d.target === ego_node) // filter only direct edges
        links.push(Object.create(d));
    }
    // MAG edges
    for (var i = 0; i < viewgraph.links_f.length; i++) {
      var d = viewgraph.links_f[i];
      d.type = "f";
      links.push(Object.create(d));
    }

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
      .attr("r", d => nodeRadiusWiki(d.r))
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
          .attr("y", function(d) {
            if (d.type === "w") return d.y+egoH+5;
            else return d.y-egoH+5;
          })
      allLinks
          .attr("d", d=> wikiLinkArc(d))
    });

    this.rect.on("click", function() {
      resetSelectedNode();
    })

  }

}
