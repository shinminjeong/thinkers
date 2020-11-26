import os, sys, json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import networkx as nx
from .network import get_thnet, count_paperref

def main(request):
    nodes, edges, schools = get_thnet()
    return render(request, "main.html", {
        "nodes": nodes,
        "edges": edges,
        "schools": schools
    })

@csrf_exempt
def get_author_info(request):
    print("!!!get_author_info", request.POST)
    a_from = request.POST.get("from_id")
    a_to = request.POST.get("to_id")
    return JsonResponse({"data": 0})
