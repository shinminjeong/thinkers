import os, json
import networkx as nx
import matplotlib.pyplot as plt
from itertools import product, permutations
from operator import itemgetter
from collections import Counter
from .search import *

cur_path = os.path.dirname(os.path.abspath(__file__))
def search_philosopher_from_MAG():
    data = json.load(open("data/philosophers.json", "r"))
    data = clean(data)
    for i, p in enumerate(data):
        pname = p["name"] if p["name"] else ""
        authorinfo = es_search_author_name(pname) if pname else None
        if authorinfo and authorinfo["PaperCount"] > 10:
            p["MAG_id"] = authorinfo["AuthorId"]
            p["MAG_name"] = authorinfo["DisplayName"]
            p["MAG_pcount"] = authorinfo["PaperCount"]
            p["MAG_ccount"] = authorinfo["CitationCount"]
            print(i, "[{}]".format(pname), p["MAG_name"], p["MAG_id"], p["MAG_pcount"], p["MAG_ccount"])
        else:
            print(i, "[{}]".format(pname), "Not Found")
    json.dump(data, open("data/philosophers_MAG.json", "w"))


def load_philosopher_net():
    print("load_philosopher_net -- start loading")
    G = nx.DiGraph()
    data = json.load(open("data/philosophers_MAG.json", "r"))
    data = clean(data)

    for i, p in enumerate(data):
        pid = p["pageid"]
        ptime = p["born"] if p["born"] else 0
        pname = p["name"] if p["name"] else ""
        pschool = ";".join([handle_school_name(s["name"]) for s in p["school"]]) if p["school"] else ""
        if "MAG_id" in p:
            G.add_node(pid, born=ptime, name=pname, school=pschool, authorid=p["MAG_id"], pcount=p["MAG_pcount"], ccount=p["MAG_ccount"])
        else:
            G.add_node(pid, born=ptime, name=pname, school=pschool)

    for i, p in enumerate(data):
        if p["influenced"]:
            for e in p["influenced"]:
                G.add_edge(e["pageid"], p["pageid"])
        if p["influences"]:
            for e in p["influences"]:
                G.add_edge(p["pageid"], e["pageid"])

    nx.write_gexf(G, "data/philosophers.gexf")
    print("load_philosopher_net -- finish")
    return

def handle_school_name(name):
    lname = name.lower()
    lname = lname.replace(" philosophy", "") # e.g. analytic == analitic philosophy
    lname = lname.replace("analytical", "analytic")
    lname = lname.replace("aristotelianism", "aristotelian")
    lname = lname.replace("realist", "realism")
    lname = lname.replace("hegelianism", "hegelian")
    lname = lname.replace("phenomenological", "phenomenology")
    lname = lname.replace("phenomenalism", "phenomenology")
    lname = lname.replace("post-kantianism", "post-kantian")
    return lname

# data cleaning rule
# https://github.com/S4N0I/theschoolofathens/blob/master/build_graph/transform.py
def clean(data):
    filtered = list(filter(filter_with_born_bound, data))
    for item in filtered:
        item['influences'] = list(filter(filter_item, item['influences']))
        item['influenced'] = list(filter(filter_item, item['influenced']))
        handle_born_corner_cases(item)
        handle_name_corner_cases(item)
    return filtered

def filter_item(item):
    return item['name'] is not None and item['pageid'] is not None

def filter_with_born_bound(item):
    return filter_item(item) and item['born'] is not None and item['born'] >= -1000000000000

# data cleaning rule
# https://github.com/S4N0I/theschoolofathens/blob/master/build_graph/transform.py
def handle_born_corner_cases(item):
    if 'Mikhail Bakhtin' in item['name']:
        item['born'] = -2366755200
    if 'Adolf von Harnack' in item['name']:
        item['born'] = -3755289600
    if 'Nicolai Hartmann' in item['name']:
        item['born'] = -2776982400
    if 'Richard Hooker' in item['name']:
        item['born'] = -13127702400
    if 'David Hume' in item['name']:
        item['born'] = -8173267200
    if 'Hermann Graf von Keyserling' in item['name']:
        item['born'] = -2840140800
    if 'Salomon Maimon' in item['name']:
        item['born'] = -6847804800
    if 'Maimonides' in item['name']:
        item['born'] = -26350099200
    if 'Wilhelm Ostwald' in item['name']:
        item['born'] = -3692131200
    if 'Ioane Petritsi' in item['name']:
        item['born'] = -30610224000
    if 'Petar II Petrović-Njegoš' in item['name']:
        item['born'] = -4954435200
    if 'Joseph Priestley' in item['name']:
        item['born'] = -7478956800
    if 'Vasily Rozanov' in item['name']:
        item['born'] = -3597523200
    if 'Adam Smith' in item['name']:
        item['born'] = -7794576000
    if 'Frederick Robert Tennant' in item['name']:
        item['born'] = -3281904000
    if 'Udayana' in item['name']:
        item['born'] = -33765897600

# data cleaning rule
# https://github.com/S4N0I/theschoolofathens/blob/master/build_graph/transform.py
def handle_name_corner_cases(item):
    if item['pageid'] == '1254755':
        item['name'] = 'Abdolkarim Soroush'
    if item['pageid'] == '16340':
        item['name'] = 'Jean-Paul Sartre'
    if item['pageid'] == '251240':
        item['name'] = 'Emil Cioran'
    if item['pageid'] == '59041318':
        item['name'] = 'August Wilhelm Rehberg'


def histogram(data):
    print([(k, 10*int(t/36000/24/365+197)) for k, t in data.items()])
    years = [10*int(t/36000/24/365+197) for t in data.values()]
    plt.hist(years, bins="auto")
    plt.title("Number of philosophers who have author id in MAG")
    plt.savefig("hist_ph_aid.png")

def save_papers_from_authorid(authorlist):
    data = {}
    for i, a in enumerate(authorlist):
        print("{}/{}".format(i, len(authorlist)))
        data[a] = es_search_papers_from_aid(a)
    json.dump(data, open("data/authorpapers.json", "w"))


def reference_btw_authors(a_from, a_to):
    load_philosopher_net();
    G = nx.read_gexf("data/philosophers.gexf")

    edges = G.edges()
    nodes = G.nodes()
    edge_data = {}
    for i, e in enumerate(edges):
        if i < a_from or i >= a_to: continue
        a1 = nodes[e[0]]
        a2 = nodes[e[1]]
        if "authorid" in a1 and "authorid" in a2:
            refcount1 =  count_paperref(a1["authorid"], a2["authorid"])
            print("{}/{}".format(i, len(edges)), a1["name"], "-->", a2["name"], refcount1)
            if refcount1 > 0:
                edge_data["{}_{}".format(a1["authorid"], a2["authorid"])] = refcount1

            refcount2 = count_paperref(a2["authorid"], a1["authorid"])
            print("{}/{}".format(i, len(edges)), a2["name"], "-->", a1["name"], refcount2)
            if refcount2 > 0:
                edge_data["{}_{}".format(a2["authorid"], a1["authorid"])] = refcount2

    json.dump(edge_data, open("data/edges_{}_{}.json".format(a_from, a_to), "w"))


def school_analysis(data):
    school_map = {}
    school_name = []
    for id, value in data.items():
        schools = value.split(";")
        if len(schools) == 0 or schools[0] == "":
            continue

        school_name.extend(schools)
        for s in schools:
            if s not in school_map:
                school_map[s] = []
            school_map[s].append(id)

    top_school_names = Counter(school_name).most_common(20)
    top_schools = {s[0]:{"rank":i, "list":school_map[s[0]]} for i, s in enumerate(top_school_names)}
    print(top_schools)
    return top_schools


def get_thnet():
    # search_philosopher_from_MAG()
    load_philosopher_net()
    G = nx.read_gexf("data/philosophers.gexf")
    ntime = nx.get_node_attributes(G, "born")
    n_school = nx.get_node_attributes(G, "school")
    n_authorid = nx.get_node_attributes(G, "authorid")
    n_pcount = nx.get_node_attributes(G, "pcount")
    n_ccount = nx.get_node_attributes(G, "ccount")
    # histogram({k:ntime[k] for k,a in n_authorid.items()})

    print("All nodes and edges:", len(G.nodes), len(G.edges), len(n_authorid))
    # save_papers_from_authorid(n_authorid.values())
    # reference_btw_authors(G)

    schools = school_analysis(n_school)
    filtered_nodes = [n for n in G.nodes() if n in ntime] # filter out node without born_time

    node_info = {n:{
        "id": n,
        "authorid": n_authorid[n] if n in n_authorid else 0,
        "pcount": n_pcount[n] if n in n_pcount else 0,
        "ccount": n_ccount[n] if n in n_ccount else 0,
        "degree": G.degree[n],
        "school": n_school[n] if n in n_school else "",
    } for n in filtered_nodes}
    return node_info, schools

pa_data = None
def count_paperref(influence_from, influence_to):
    global pa_data
    if pa_data == None:
        pa_data = json.load(open("data/authorpapers.json", "r"))

    papers_from = pa_data[str(influence_from)]
    papers_to = pa_data[str(influence_to)]
    ref_count = 0
    ref_list = ["{}_{}".format(p1, p2) for p1, p2 in product(papers_to, papers_from)]
    batch_size = 1000
    for i in range(0, len(ref_list), batch_size):
        hit = es_search_paper_reference(ref_list[i:batch_size+i])
        print("{}-->{}] {}-{}/{}".format(influence_from, influence_to, i, batch_size+i, len(ref_list)), hit)
        ref_count += hit
    return ref_count
