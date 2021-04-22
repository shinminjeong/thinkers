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

    egonode, node_w, edge_w, node_f, edge_f = get_arcnet(pageid)
    data = {
        "ego_node": egonode,
        "node_info_w": node_w,
        "edge_info_w": edge_w,
        "node_info_f": node_f,
        "edge_info_f": edge_f,
    }

    return render(request, "arc.html", data)
