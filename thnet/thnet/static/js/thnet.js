var color = d3.scaleOrdinal(d3.schemeCategory20);
var simulation, yScale, yAxisG, vis, allNodes, allLinks, allLabels;
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
    d.fx = null;
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

function createYAxis(scale) {
  return d3.axisLeft(scale)
    .ticks(10)
    .tickFormat(function(d) {
        var yearsAd = 100*Math.floor((d/(3600*24*365)+1970)/100);
        if(yearsAd >= 0) {
            return yearsAd + "";
        } else {
            return Math.abs(yearsAd) + " BC"
        }
    });
}

var selectedNode = connectedNode = null;
function nodeSelected(node) {
  if (selectedNode === node || connectedNode === node) return;
  if(selectedNode != null) { // select connected node
    allLabels.classed("show", function(n){ return n.id == node.id || n.id == selectedNode.id})
    console.log("nodeSelected", node.getAttribute("title"), node.classList.contains("influences"), node.classList.contains("influenced-by"))
    connectedNode = node;
    if (node.getAttribute("data_authorid") != "0") {
      if (node.classList.contains("influenced-by"))
        getAuthorInfo(selectedNode, connectedNode);
      if (node.classList.contains("influences"))
        getAuthorInfo(connectedNode, selectedNode);
    }

  } else { // select the center node
    console.log("nodeSelected", node.id, node.getAttribute("title"), node)
    allNodes.classed("selected", function(n){ return n.id == node.id});
    allLinks.classed("influenced-by", function(l){ return l.target.id == node.id})
    allLinks.classed("influences", function(l){ return l.source.id == node.id})
    allLabels.classed("show", function(n){ return n.id == node.id})
    d3.selectAll(".link.influenced-by").each(function(d, l) {
      d3.select(allNodes._groups[0][d.source.index]).classed("influenced-by", true);
      // d3.select(allLabels._groups[0][d.source.index]).classed("show", true);
    });
    d3.selectAll(".link.influences").each(function(d, l) {
      d3.select(allNodes._groups[0][d.target.index]).classed("influences", true);
      // d3.select(allLabels._groups[0][d.target.index]).classed("show", true);
    });
    selectedNode = node;
  }
}

function resetSelectedNode() {
  selectedNode = connectedNode = null;
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
  if (selectedNode === node || connectedNode === node) return;
  d3.select('text[id="'+node.id+'"]').classed("show", false);
}


function highlightSchool(school_name) {
  var philosophers = schoolgroups[school_name];
  console.log("highlightSchool", philosophers)
  for (var i = 0; i < philosophers.length; i++) {
    d3.select('circle[id="'+philosophers[i]+'"]').classed("selected", true);
  }
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

  drawGraph() {
    const min_radius = 1;
    const yScale_margin = 80;

    const timestamps = viewgraph.nodes.map(d => d.born);

    // add Y axis
    yScale = d3.scaleLinear()
      .domain(d3.extent(timestamps)).nice()
      .range([this.height - yScale_margin, yScale_margin]);
    var yAxis = createYAxis(yScale)

    yAxisG = this.outer.append("g")
      .classed('y-axis', true)
      .call(yAxis)
      .attr("display", "block")
      .attr("transform", "translate(" + (this.width * 0.08 + 38) + "," + 0 + ")");


    for (var i = 0; i < viewgraph.nodes.length; i++) {
      viewgraph.nodes[i].savedFy = yScale(viewgraph.nodes[i].born);
      viewgraph.nodes[i].fy = yScale(viewgraph.nodes[i].born);
    }

    const links = viewgraph.links.map(d => Object.create(d));
    const nodes = viewgraph.nodes.map(d => Object.create(d));

    // draw force directed network
    simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id))
      .force("charge", d3.forceManyBody())
      .force("center", d3.forceCenter(this.width / 2, this.height / 2));

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
      .attr("savedFy", d => yScale(d.born))
      .attr("r", d => Math.max(min_radius, Math.sqrt(d.degree)))
      .on("click", function() {
        nodeSelected(this);
      })
      .on("mouseover", function() {
        showLabel(this);
      })
      .on("mouseout", function() {
        hideLabel(this);
      })
      .call(drag(simulation));

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
    });

    this.rect.on("click", function() {
      resetSelectedNode();
    })

  }

}
