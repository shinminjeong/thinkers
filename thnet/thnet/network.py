import os, json, csv
import networkx as nx
import matplotlib.pyplot as plt
from itertools import product, permutations
from operator import itemgetter
from collections import Counter
from .search import *

cur_path = os.path.dirname(os.path.abspath(__file__))
def search_philosopher_from_MAG():
    print("search_philosopher_from_MAG")
    data = json.load(open("data/philosophers.json", "r"))
    data = clean(data)
    mag_cleaned = csv.reader(open("philosophers_MAG_cleaned.csv"))
    next(mag_cleaned)
    next(mag_cleaned)
    mag_data = {r[0]: {
        "name": r[1],
        "year": r[2],
        "author_id": r[3],
        "author_name": r[4]
    } for r in mag_cleaned}

    for i, p in enumerate(data):
        pname = p["name"] if p["name"] else ""
        pageid = p["pageid"]
        if pageid in mag_data:
            pyear = mag_data[pageid]["year"]
            authorid = mag_data[pageid]["author_id"]
            if authorid != "no info" and int(pyear) >= 1750:
                authorinfo = es_search_author_id(authorid)
                if authorinfo == None:
                    print(i, "[{}] -- {}".format(pname, authorid), "Not in current DB")
                    continue
                p["MAG_id"] = authorinfo["AuthorId"]
                p["MAG_name"] = authorinfo["DisplayName"]
                p["MAG_pcount"] = authorinfo["PaperCount"]
                p["MAG_ccount"] = authorinfo["CitationCount"]
                print(i, "[{}]".format(pname), p["MAG_name"], p["MAG_id"], p["MAG_pcount"], p["MAG_ccount"])
            else:
                print(i, "[{}] -- {}, {}".format(pname, authorid, pyear), "Not Found")
        else:
            print(i, "[{}]".format(pname), "Not in MAG")
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
        pschool = ",".join([create_school_map(s["pageid"], s["name"]) for s in p["school"]]) if p["school"] else ""
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

school_name_map = {}
def create_school_map(school_id, name):
    global school_name_map
    if school_id == None:
        return "noinfo"
    if school_id not in school_name_map:
        school_name_map[school_id] = name;
    return school_id

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


def school_analysis(data, filtered_nodes):
    global school_name_map
    school_philosopher_map = {}
    for id, value in data.items():
        schools = value.split(",")
        for s in schools:
            if s not in school_philosopher_map:
                school_philosopher_map[s] = []
            if id in filtered_nodes:
                school_philosopher_map[s].append(id)

    school_counts = [(k, len(v)) for k, v in school_philosopher_map.items() if k != "" and k != "noinfo"]
    top_school_names = sorted(school_counts, key=itemgetter(1), reverse=True)[:20]
    top_schools = {s[0]:{"name":school_name_map[s[0]], "rank":i, "list":school_philosopher_map[s[0]]} for i, s in enumerate(top_school_names)}
    # print(top_schools)
    return top_schools


def ref_edge(G, aidmap, filtered_nodes):
    edge_info = []
    for u, v in G.edges():
        if u not in filtered_nodes or v not in filtered_nodes:
            continue
        edge = {
            "source": u,
            "target": v,
            "value": 1
        }
        edge_info.append(edge)
    # print(sum(e2_sum), sum(e1_sum))
    print("edges", len(G.edges()), len(edge_info))
    return edge_info


def born_year(time):
    return int(time/(3600*24*365)+1970)

def born_time(year):
    return (int(year)-1970)*(3600*24*365)



def get_th_egonet(pageid):
    print("get_egonet", pageid)
    G = nx.read_gexf("data/philosophers.gexf")
    egoG = nx.ego_graph(G, pageid, undirected=True)

    ntime = nx.get_node_attributes(G, "born")
    n_name = nx.get_node_attributes(G, "name")
    n_school = nx.get_node_attributes(G, "school")
    n_authorid = nx.get_node_attributes(G, "authorid")
    n_pcount = nx.get_node_attributes(G, "pcount")
    n_ccount = nx.get_node_attributes(G, "ccount")
    filtered_nodes = [n for n in egoG.nodes() if n in ntime]

    pagerank = nx.pagerank(G)
    node_info = [{
        "id": n,
        "name": n_name[n],
        "authorid": n_authorid[n] if n in n_authorid else 0,
        "born": ntime[n],
        "pcount": n_pcount[n] if n in n_pcount else 0,
        "ccount": n_ccount[n] if n in n_ccount else 0,
        "r": round(pagerank[n], 9),
        "school": n_school[n] if n in n_school else "",
    } for n in filtered_nodes]
    edge_info = ref_edge(egoG, n_authorid, filtered_nodes)

    print("node_info", node_info)
    print("edge_info", edge_info)

    return node_info, edge_info

def get_arcnet(pageid):
    print("get_egonet", pageid)
    G = nx.read_gexf("data/philosophers.gexf")
    egoG = nx.ego_graph(G, pageid, undirected=True)

    ntime = nx.get_node_attributes(G, "born")
    n_name = nx.get_node_attributes(G, "name")
    n_school = nx.get_node_attributes(G, "school")
    n_authorid = nx.get_node_attributes(G, "authorid")
    n_pcount = nx.get_node_attributes(G, "pcount")
    n_ccount = nx.get_node_attributes(G, "ccount")
    filtered_nodes = [n for n in egoG.nodes() if n in ntime]

    pagerank = nx.pagerank(G)
    node_info_w = [{
        "id": n,
        "name": n_name[n],
        "authorid": n_authorid[n] if n in n_authorid else 0,
        "born": ntime[n],
        "r": round(pagerank[n], 9),
    } for n in filtered_nodes]
    edge_info_w = ref_edge(egoG, n_authorid, filtered_nodes)

    # timeline of the ego
    ego_timeline = [{"type":"born", "year":ntime[pageid], "count":1}]

    ego_authorid = n_authorid[pageid]
    flower_data = json.load(open("data/flowers/{}.json".format(ego_authorid), "r"))
    # print(flower_data)

    node_info_f = {}
    edge_info_f = []
    pub_timeline = []
    for i, f in enumerate(flower_data):
        for y in f["year"]:
            pubyear = y["publication_year"]
            infyear = y["influence_year"]
            name = f["entity_name"]
            idx = i+1
            if y["influencing"] > 0:
                node_id = "{}_{}_{}".format(name, pubyear, idx)
                if node_id in node_info_f:
                    node_info_f[node_id]["r"] += y["influencing"]/1000
                else:
                    node_info_f[node_id] = {
                        "id": "{}_{}_{}".format(name, pubyear, idx),
                        "node": "alt",
                        "index": idx,
                        "name": name,
                        "born": born_time(pubyear),
                        "r": y["influencing"]/1000
                    }
                pub_timeline.append(infyear)
                print(infyear, "<--", pubyear, name, y)
                edge_info_f.append({
                    "source": "{}_{}_{}".format(name, pubyear, idx),
                    "target": "ego_{}".format(infyear),
                    "direction": "influencing",
                    "value": y["influencing"]
                })
            if y["influenced"] > 0:
                node_id = "{}_{}_{}".format(name, infyear, idx)
                if node_id in node_info_f:
                    node_info_f[node_id]["r"] += y["influenced"]/1000
                else:
                    node_info_f[node_id] = {
                        "id": "{}_{}_{}".format(name, infyear, idx),
                        "node": "alt",
                        "index": idx,
                        "name": name,
                        "born": born_time(infyear),
                        "r": y["influenced"]/1000
                    }
                pub_timeline.append(pubyear)
                print(infyear, "-->", pubyear, name, y)
                edge_info_f.append({
                    "source": "{}_{}_{}".format(name, infyear, idx),
                    "target": "ego_{}".format(pubyear),
                    "direction": "influenced",
                    "value": y["influenced"]
                })

    pub_cnt = Counter(pub_timeline)
    for pubyear in pub_timeline:
        node_info_f["ego_{}".format(pubyear)] = {
            "id": "ego_{}".format(pubyear, idx),
            "node": "ego",
            "index": 0,
            "born": born_time(pubyear),
            "r": pub_cnt[pubyear]/1000
        }
    # print("node_info_w", node_info_w)
    # print("edge_info_w", edge_info_w)
    # print("node_info_f", node_info_f.values())
    # print("edge_info_f", edge_info_f)

    return node_info_w, edge_info_w, list(node_info_f.values()), edge_info_f

def get_thnet(time):
    # search_philosopher_from_MAG()
    load_philosopher_net()
    G = nx.read_gexf("data/philosophers.gexf")
    ntime = nx.get_node_attributes(G, "born")
    n_name = nx.get_node_attributes(G, "name")
    n_school = nx.get_node_attributes(G, "school")
    n_authorid = nx.get_node_attributes(G, "authorid")
    n_pcount = nx.get_node_attributes(G, "pcount")
    n_ccount = nx.get_node_attributes(G, "ccount")
    # histogram({k:ntime[k] for k,a in n_authorid.items()})

    print("All nodes and edges:", len(G.nodes), len(G.edges), len(n_authorid))

    if time == "modern":
        filtered_nodes = [n for n in G.nodes() if n in ntime and born_year(ntime[n]) >= 1800]
    else: # time not specified or "all"
        filtered_nodes = [n for n in G.nodes() if n in ntime] # filter out node without born_time
    schools = school_analysis(n_school, filtered_nodes)

    pagerank = nx.pagerank(G)
    node_info = [{
        "id": n,
        "name": n_name[n],
        "authorid": n_authorid[n] if n in n_authorid else 0,
        "born": ntime[n],
        "pcount": n_pcount[n] if n in n_pcount else 0,
        "ccount": n_ccount[n] if n in n_ccount else 0,
        "centrality": round(pagerank[n], 9),
        "school": n_school[n] if n in n_school else "",
    } for n in filtered_nodes]
    edge_info = ref_edge(G, n_authorid, filtered_nodes)

    return node_info, edge_info, schools

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
