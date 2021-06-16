import os, sys, json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import networkx as nx
from .network import get_thnet, get_th_egonet, get_arcnet
from .flower import make_flower

def main(request):
    time = request.GET.get("time")
    print("time", time)

    node_info, edge_info, schools = get_thnet(time)
    return render(request, "main.html", {
        "node_info": node_info,
        "edge_info": edge_info,
        "schools": schools
    })

@csrf_exempt
def get_author_info(request):
    print("!!!get_author_info", request.POST)
    a_from = request.POST.get("from_id")
    a_to = request.POST.get("to_id")
    return JsonResponse({"data": 0})


def flower(request):
    pageid = request.GET.get('id')
    flower_info = make_flower(pageid)

    node_info, edge_info = get_th_egonet(pageid)
    data = {
        "ego_node": pageid,
        "node_info": node_info,
        "edge_info": edge_info,
        "author": flower_info
    }

    return render(request, "flower.html", data)

def arc(request):
    pageid = request.GET.get('id')

    egonode, charts, node_a, edge_a = get_arcnet(pageid)
    # author_nodes, author_edges = calculate_author_net(egonode, node_w, node_f, edge_w, edge_f)
    data = {
        "ego_node": egonode,
        "charts": charts,
        "node_info": node_a,
        "edge_info": edge_a,
        "papers_n": [],
        "papers_e": []
    }

    return render(request, "arc.html", data)


def calculate_author_net(egonode, node_w, node_f, edge_w, edge_f):
    node_w_set = {w["authorid"]: w for w in node_w}
    node_f_set = {f["authorid"]: f for f in node_f}
    print(egonode)

    author_nodes = node_w
    author_edges = []
    for e in edge_w:
        e["type"] = "w"
        author_edges.append(e)

    for k, v in node_f_set.items():
        pubyears = sorted([f["born"] for f in node_f if f["authorid"] == k])
        # print(k, v["name"], pubyears)

        if k in node_w_set: # if mag author also appears in wiki
            pubyears = [node_w_set[k]["born"]]+pubyears # add born year in the timeline
            print("!!! mag author also appears in wiki", k, node_w_set[k])
            if node_w_set[k]["id"] != egonode["pageid"]:
                edges_out = [e["value"] for e in edge_f if e["parent"] == k and e["direction"] == "influenced"]
                edges_in = [e["value"] for e in edge_f if e["parent"] == k and e["direction"] == "influencing"]
                print(sum(edges_out), sum(edges_in))
                if sum(edges_out) > 0:
                    author_edges.append({
                        "source": node_w_set[k]["id"],
                        "target": egonode["pageid"],
                        "type": "f",
                        "value": sum(edges_out)
                    })
                if sum(edges_in) > 0:
                    author_edges.append({
                        "source": egonode["pageid"],
                        "target": node_w_set[k]["id"],
                        "type": "f",
                        "value": sum(edges_in)
                    })
            # duplicate node for MAG timeline
            author_nodes.append({
                "id": node_w_set[k]["id"],
                "born": node_w_set[k]["born"],
                "name": node_w_set[k]["name"],
                "r": 0.005,
                "type": "f",
                "papers": pubyears
            })
        else:
            edges_out = [e["value"] for e in edge_f if e["parent"] == k and e["direction"] == "influenced"]
            edges_in = [e["value"] for e in edge_f if e["parent"] == k and e["direction"] == "influencing"]
            if sum(edges_out) > 0:
                author_edges.append({
                    "source": str(k),
                    "target": egonode["pageid"],
                    "type": "f",
                    "value": sum(edges_out)
                })
            if sum(edges_in) > 0:
                author_edges.append({
                    "source": egonode["pageid"],
                    "target": str(k),
                    "type": "f",
                    "value": sum(edges_in)
                })
            author_nodes.append({
                "id": k,
                "born": pubyears[0],
                "name": v["name"],
                "r": v["r"],
                "type": "f",
                "papers": pubyears
            })
    # print(author_edges)
    return author_nodes, author_edges
