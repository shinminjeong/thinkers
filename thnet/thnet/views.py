import os, sys, json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import networkx as nx
from .network import get_thnet
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
    data = {
        "author": flower_info,
        "conf"  : [],
        "inst"  : [],
        "fos"   : [],
    }

    return render(request, "flower.html", data)
