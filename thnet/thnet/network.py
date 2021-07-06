import os, json, csv
import networkx as nx
import matplotlib.pyplot as plt
from itertools import product, permutations
from operator import itemgetter
from collections import Counter
from .search import *
from .wikiparser import parse_page

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
        p_id = p["pageid"]
        p_time = p["born"] if p["born"] else 0
        p_name = p["name"] if p["name"] else ""
        p_url = p["url"] if p["url"] else ""
        p_img = p["img"] if p["img"] else ""
        p_school = ",".join([create_school_map(s["pageid"], s["name"]) for s in p["school"]]) if p["school"] else ""
        G.add_node(p_id, born=p_time, name=p_name, school=p_school, url=p_url, img=p_img)
        if "MAG_id" in p:
            G.nodes[p_id]["authorid"]=p["MAG_id"]
            G.nodes[p_id]["pcount"]=p["MAG_pcount"]
            G.nodes[p_id]["ccount"]=p["MAG_ccount"]

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


def ref_edge(G, filtered_nodes):
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
    edge_info = ref_edge(egoG, filtered_nodes)

    print("node_info", node_info)
    print("edge_info", edge_info)

    return node_info, edge_info

def get_ph_info(url):
    return parse_page(url)

def agg_citation(citations):
    data = {k["year"]:0 for k in citations}
    for values in citations:
        for v in values["value"]:
            data[v["year"]] += v["value"]
    return [{"year":y, "value":v} for y, v in data.items()]


def create_edge_f(source, target, dir, parent, value):
    return {
        "source": source,
        "target": target,
        "direction": dir,
        "type": "MAG",
        "parent": parent,
        "value": value
    }


def get_seqnet(pageid):
    load_philosopher_net()
    print("get_seqnet", pageid)
    G = nx.read_gexf("data/philosophers.gexf")
    N = G.nodes
    pagerank = nx.pagerank(G)
    egoG = nx.ego_graph(G, pageid, undirected=True)
    ego = {
        "pageid": pageid,
        "name": N[pageid]["name"],
        "authorid": N[pageid]["authorid"],
        "born": N[pageid]["born"],
        "url": N[pageid]["url"],
        "image": N[pageid]["img"],
        "info": get_ph_info(N[pageid]["url"])
    }

    filtered_nodes = [n for n in egoG.nodes() if "born" in N[n]]
    node_authors = [{
        "id": n,
        "name": N[n]["name"],
        "authorid": N[n]["authorid"] if "authorid" in N[n] else 0,
        "type": "WIKI",
        "born": N[n]["born"],
        "r": round(pagerank[n], 9),
    } for n in filtered_nodes]

    edge_authors = ref_edge(egoG, filtered_nodes)
    flower_data = json.load(open("data/flowers/{}.json".format(ego["authorid"]), "r"))

    # add flower data
    radius_scale = 1500
    wiki_authorids = [a["authorid"] for a in node_authors]
    flower_ego_id = pageid
    for i, f in enumerate(flower_data["flower"]):
        # create node for each alter
        aid_s, name = f["entity_name"].split(";")
        aid = int(aid_s)
        node_id = aid
        pubtimes = [born_time(y["publication_year"]) for y in f["year"] if y["influencing"]>0]
        inftimes = [born_time(y["influence_year"]) for y in f["year"] if y["influenced"]>0]
        min_time = min(pubtimes+inftimes)

        if f["influencing"] > 0:
            edge_authors.append(create_edge_f(flower_ego_id, node_id, "influencing", aid, f["influencing"]))
        if f["influenced"] > 0:
            edge_authors.append(create_edge_f(node_id, flower_ego_id, "influenced", aid, f["influenced"]))

        # if the author also exists in Wiki data
        # change the min_time to born_time
        if aid in wiki_authorids:
            wauthor = [a for a in node_authors if a["authorid"] == aid][0]
            print("!!!!!!!!", name, aid, "also exists in Wiki data")
            print(wauthor)
            min_time = wauthor["born"]

        node_authors.append({
            "id": node_id,
            "authorid": aid,
            "type": "MAG",
            "name": name,
            "born": min_time,
            "pubtimes": pubtimes,
            "inftimes": inftimes,
            "r": (f["influencing"]+f["influenced"])/radius_scale
        })

    charts = {
        "pub_chart": flower_data["pub_chart"],
        "cite_chart": agg_citation(flower_data["cite_chart"]),
        "cite_detail": flower_data["cite_chart"]
    }

    return ego, charts, node_authors, edge_authors


def get_arcnet(pageid):
    load_philosopher_net()
    print("get_arcnet", pageid)
    G = nx.read_gexf("data/philosophers.gexf")
    N = G.nodes
    pagerank = nx.pagerank(G)
    egoG = nx.ego_graph(G, pageid, undirected=True)
    ego = {
        "pageid": pageid,
        "name": N[pageid]["name"],
        "authorid": N[pageid]["authorid"],
        "born": N[pageid]["born"],
        "url": N[pageid]["url"],
        "image": N[pageid]["img"],
        "info": get_ph_info(N[pageid]["url"])
    }

    filtered_nodes = [n for n in egoG.nodes() if "born" in N[n]]
    node_authors = [{
        "id": n,
        "name": N[n]["name"],
        "authorid": N[n]["authorid"] if "authorid" in N[n] else 0,
        "type": "WIKI",
        "born": N[n]["born"],
        "r": round(pagerank[n], 9),
    } for n in filtered_nodes]
    edge_authors = ref_edge(egoG, filtered_nodes)
    flower_data = json.load(open("data/flowers/{}.json".format(ego["authorid"]), "r"))

    # add flower data
    radius_scale = 1500
    wiki_authorids = [a["authorid"] for a in node_authors]
    flower_ego_id = "{}_mag".format(pageid)
    for i, f in enumerate(flower_data["flower"]):
        # create node for each alter
        aid_s, name = f["entity_name"].split(";")
        aid = int(aid_s)
        node_id = "{}_mag".format(aid)
        pubtimes = [born_time(y["publication_year"]) for y in f["year"] if y["influencing"]>0]
        inftimes = [born_time(y["influence_year"]) for y in f["year"] if y["influenced"]>0]
        min_time = min(pubtimes+inftimes)

        # if the author also exists in Wiki data
        # change the min_time to born_time
        if aid in wiki_authorids:
            wauthor = [a for a in node_authors if a["authorid"] == aid][0]
            # print("!!!!!!!!", name, aid, "also exists in Wiki data")
            # print(wauthor)
            min_time = wauthor["born"]

        if f["influencing"] > 0:
            edge_authors.append(create_edge_f(flower_ego_id, node_id, "influencing", aid, f["influencing"]))
        if f["influenced"] > 0:
            edge_authors.append(create_edge_f(node_id, flower_ego_id, "influenced", aid, f["influenced"]))

        node_authors.append({
            "id": node_id,
            "authorid": aid,
            "type": "MAG",
            "name": name,
            "born": min_time,
            "pubtimes": pubtimes,
            "inftimes": inftimes,
            "r": (f["influencing"]+f["influenced"])/radius_scale
        })


    # add egonode for flower
    node_authors.append({
        "id": flower_ego_id,
        "authorid": ego["authorid"],
        "type": "MAG",
        "name": ego["name"],
        "born": ego["born"],
    })

    # add egonode for publication timeline
    node_authors.append({
        "id": "{}_pub".format(pageid),
        "authorid": ego["authorid"],
        "type": "PUB",
        "name": ego["name"],
        "born": ego["born"],
    })

    charts = {
        "pub_chart": flower_data["pub_chart"],
        "cite_chart": agg_citation(flower_data["cite_chart"]),
        "cite_detail": flower_data["cite_chart"]
    }

    return ego, charts, node_authors, edge_authors

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
    edge_info = ref_edge(G, filtered_nodes)

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
