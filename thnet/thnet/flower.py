import os, json
import networkx as nx
import pandas as pd
from itertools import product, permutations
from operator import itemgetter
from collections import Counter
from .agg_score import *
from .entity_type import Entity_type
from .flower_bloom_data import score_df_to_graph

def default_config():
    return {
        'self_cite': False,
        'icoauthor': True,
        'pub_lower': None,
        'pub_upper': None,
        'cit_lower': None,
        'cit_upper': None,
        'num_leaves': 25,
        'order': 'ratio',
    }

def make_flower(pageid):
    G = nx.read_gexf("data/philosophers.gexf")
    print("All nodes and edges:", len(G.nodes), len(G.edges))
    egonode = G.nodes()[pageid]
    egoname = normalized_name(egonode["name"])

    paper_information = create_papers(pageid, G)
    score_df = score_paper_info_list(paper_information, self=[egoname])

    flower_type = ('author', [Entity_type.AUTH])
    flower = gen_flower_data(score_df, flower_type, [egoname], egoname, config=default_config())
    return flower

def normalized_name(name):
    name = name.replace("'", " ")
    name = name.replace(",", "")
    return name

def dummy_paperinfo(paperid, authorid, authorname):
    return {
        'Year': 1990,
        'JournalId': 0,
        'PaperTitle': '',
        'PaperId': paperid,
        'JournalName': 'journal',
        'Authors': [{
            'AuthorId': authorid,
            'AuthorName': authorname,
        }],
        'FieldsOfStudy': [],
    }

def create_papers(pageid, G):
    nodes = G.nodes()
    id_count = 0
    paper_information = []
    references = []
    citations = []
    for u,v in G.out_edges(pageid):
        if "name" not in nodes[v] or u != pageid: continue
        references.append(dummy_paperinfo(int(G[u][v]["id"]), nodes[v]["label"], normalized_name(nodes[v]["name"])))
    for u,v in G.in_edges(pageid):
        id_count = id_count+1
        if "name" not in nodes[u] or v != pageid: continue
        citations.append(dummy_paperinfo(int(G[u][v]["id"]), nodes[u]["label"], normalized_name(nodes[u]["name"])))

    paper = dummy_paperinfo(0, pageid, normalized_name(nodes[pageid]["name"]))
    paper["References"] = references
    paper["Citations"] = citations

    print(paper["Authors"])
    print("reference:", [r["Authors"][0]["AuthorId"] for r in references])
    print("citation:", [r["Authors"][0]["AuthorId"] for r in citations])

    paper_information.append(paper)

    # print(paper_information)
    return paper_information


def to_influence_dict(name, infed, infing):
    '''
    '''
    return {
            'entity_name': name,
            'influenced' : infed,
            'influencing': infing
            }

def score_paper_info_list(paper_info_list, self=list()):
    '''
    '''
    # Query results
    score_list = {
        'CONF': list(),
        'JOUR': list(),
        'AFFI': list(),
        'AUTH': list(),
        'FSTD': list(),
    }

    # Turn paper information into score dictionary
    for paper_info in paper_info_list:
        single_score = score_paper_info(paper_info, self)
        for k, v in single_score.items():
            score_list[k] += v

    # Score dataframe
    return score_list


def score_paper_info(paper_info, self=list()):
    '''
    '''
    # Score results
    score_list = {
            'CONF': list(),
            'JOUR': list(),
            'AFFI': list(),
            'AUTH': list(),
            'FSTD': list(),
            }

    ###  COAUTHOR DUMMY VALUES ###
    coauthor_const = {
        'self_cite': False,
        'coauthor': True,
        'publication_year': paper_info['Year'] if 'Year' in paper_info else None,
        'influence_year': paper_info['Year'] if 'Year' in paper_info else None,
        'ego_paper_id': int(paper_info['PaperId']),
        'link_paper_id': int(paper_info['PaperId'])
    }

    make_dummy = lambda x: dict(**to_influence_dict(x, 0, 0), **coauthor_const)

    # Get venue value
    if 'ConferenceName' in paper_info:
        score_list['CONF'].append(make_dummy(paper_info['ConferenceName']))
    if 'JournalName' in paper_info:
        score_list['JOUR'].append(make_dummy(paper_info['JournalName']))

    # Get author combinations
    for paa in paper_info['Authors']:
        if 'AuthorName' in paa:
            score_list['AUTH'].append(make_dummy(paa['AuthorName']))
        if 'AffiliationName' in paa:
            score_list['AFFI'].append(make_dummy(paa['AffiliationName']))

    # Get fos fields
    try:
        for pfos in paper_info['FieldsOfStudy']:
            if 'FieldOfStudyName' in pfos and pfos['FieldOfStudyLevel'] == 1:
                score_list['FSTD'].append(make_dummy(pfos['FieldOfStudyName']))
    except:
        print(paper_info['PaperId'])
    ###  COAUTHOR DUMMY VALUES ###

    ###  REFERENCE VALUES ###
    # Calculate references influence
    for reference in paper_info['References']:
        # Check if it is a self citation
        ref_const = {
            'self_cite': is_self_cite(reference, self),
            'coauthor': False,
            'publication_year': paper_info['Year'] if 'Year' in paper_info else None,
            'influence_year': paper_info['Year'] if 'Year' in paper_info else None,
            'ego_paper_id': int(paper_info['PaperId']),
            'link_paper_id': int(reference['PaperId'])
        }

        make_score = lambda x: dict(**to_influence_dict(*x), **ref_const)

        # Get venue value
        if 'ConferenceName' in reference:
            score_list['CONF'].append(make_score((reference['ConferenceName'], 0, 1)))
        if 'JournalName' in reference:
            score_list['JOUR'].append(make_score((reference['JournalName'], 0, 1)))

        # Get author combinations
        influencing_paa = 1 / len(reference['Authors'])
        for paa in reference['Authors']:
            if 'AuthorName' in paa:
                score_list['AUTH'].append(make_score((paa['AuthorName'], 0, influencing_paa)))
            if 'AffiliationName' in paa:
                score_list['AFFI'].append(make_score((paa['AffiliationName'], 0, influencing_paa)))

        # Get fos fields
        try:
            for pfos in reference['FieldsOfStudy']:
                if 'FieldOfStudyName' in pfos and pfos['FieldOfStudyLevel'] == 1:
                    score_list['FSTD'].append(make_score((pfos['FieldOfStudyName'], 0, 1)))
        except:
            print(paper_info['PaperId'], reference['PaperId'])
    ###  REFERENCE VALUES ###


    ###  CITATION VALUES ###

    # Calculate the influenced score for paa (for this paper)
    influenced_paa = 1 / len(paper_info['Authors']) if 'Authors' in paper_info else 1

    # Calculate citation influence (influenced)
    for citation in paper_info['Citations']:
        # Check if it is a self citation
        cit_const = {
            'self_cite': is_self_cite(citation, self),
            'coauthor': False,
            'publication_year': paper_info['Year'] if 'Year' in paper_info else None,
            'influence_year': citation['Year'] if 'Year' in paper_info else None,
            'ego_paper_id': int(paper_info['PaperId']),
            'link_paper_id': int(citation['PaperId'])
        }

        make_score = lambda x: dict(**to_influence_dict(*x), **cit_const)

        # Get venue value
        if 'ConferenceName' in citation:
            score_list['CONF'].append(make_score((citation['ConferenceName'], 1, 0)))
        if 'JournalName' in citation:
            score_list['JOUR'].append(make_score((citation['JournalName'], 1, 0)))

        # Get author combinations
        influencing_paa = 1 / len(citation['Authors'])
        for paa in citation['Authors']:
            if 'AuthorName' in paa:
                score_list['AUTH'].append(make_score((paa['AuthorName'], influenced_paa, 0)))
            if 'AffiliationName' in paa:
                score_list['AFFI'].append(make_score((paa['AffiliationName'], influenced_paa, 0)))

        # Get fos fields
        for pfos in citation['FieldsOfStudy']:
            if 'FieldOfStudyName' in pfos and pfos['FieldOfStudyLevel'] == 1:
                score_list['FSTD'].append(make_score((pfos['FieldOfStudyName'], 1, 0)))
    ###  CITATION VALUES ###

    return score_list


def is_self_cite(paper_prop, self):
    ''' Determines if a paper property is a self citation depending on a list
        of self names.
    '''
    # If no self names
    if not self:
        return False

    names = list()

    # Get all author names and affiliation names
    if 'Authors' in paper_prop:
        for author in paper_prop['Authors']:
            if 'AuthorName' in author:
                names.append(author['AuthorName'])
            if 'AffiliationName' in author:
                names.append(author['AffiliationName'])

    # Get field of study names
    if 'FieldOfStudy' in paper_prop:
        for fos in paper_prop['FieldOfStudy']:
            if 'FieldOfStudyName' in fos:
                names.append(fos['FieldOfStudyName'])

    # Add other potential fields
    fields = ['ConferenceName', 'JournalName']
    for field in fields:
        if field in paper_prop:
            names.append(paper_prop[field])

    return any(i in self for i in names)


def score_leaves(score_list, leaves):
    '''
    '''
    DF_COLUMNS = [
        'entity_name',
        'entity_type',
        'influence_year',
        'publication_year',
        'self_cite',
        'coauthor',
        'influenced',
        'influencing',
        'ego_paper_id',
        'link_paper_id'
    ]
    score_df = pd.DataFrame(columns = DF_COLUMNS)

    for leaf in leaves:
        if (score_list[leaf.ident]):
            score_df = score_df.append(score_list[leaf.ident], ignore_index=True)

    score_df['self_cite'] = score_df['self_cite'].astype('bool')
    score_df['coauthor'] = score_df['coauthor'].astype('bool')

    return score_df


def gen_flower_data(score_df, flower_prop, entity_names, flower_name,
                    config=default_config):
    '''
    '''
    # Flower properties
    flower_type, leaves = flower_prop
    print('[gen_flower_data] flower_type', flower_type)

    t1 = datetime.now()
    print(datetime.now(), 'start score_leaves')
    entity_score = score_leaves(score_df, leaves)
    print(datetime.now(), 'finish score_leaves')

    # Ego name removal
    if (flower_type != 'conf'):
        entity_score = entity_score[~entity_score['entity_name'].str.lower()\
                .isin(entity_names)]

    t2 = datetime.now()
    # Aggregate
    agg_score = agg_score_df(entity_score)
    # print(agg_score)

    # Select the influence type from self citations
    if config['self_cite'] and config['icoauthor']:
        agg_score['influenced'] = agg_score.influenced_tot
        agg_score['influencing'] = agg_score.influencing_tot
    elif config['self_cite']:
        agg_score['influenced'] = agg_score.influenced_nca
        agg_score['influencing'] = agg_score.influencing_nca
    elif config['icoauthor']:
        agg_score['influenced'] = agg_score.influenced_nsc
        agg_score['influencing'] = agg_score.influencing_nsc
    else:
        agg_score['influenced'] = agg_score.influenced_nscnca
        agg_score['influencing'] = agg_score.influencing_nscnca

    # Sort alphabetical first
    agg_score.sort_values('entity_name', ascending=False, inplace=True)

    # Sort by sum of influence
    agg_score['tmp_sort'] = agg_score.influencing + agg_score.influenced
    agg_score.sort_values('tmp_sort', ascending=False, inplace=True)

    # Sort by max of influence
    agg_score['tmp_sort'] = np.maximum(agg_score.influencing, agg_score.influenced)
    agg_score.sort_values('tmp_sort', ascending=False, inplace=True)
    agg_score.drop('tmp_sort', axis=1, inplace=True)

    # Need to take empty df into account
    if agg_score.empty:
        top_score = agg_score
        num_leaves = config['num_leaves']
    else:
        num_leaves = max(50, config['num_leaves'])
        top_score = agg_score.head(n=num_leaves)

    # Calculate post filter statistics (sum and ratio)
    top_score = post_agg_score_df(top_score)
    top_score.ego = flower_name

    # Calculate the bloom ordering
    top_score['bloom_order'] = range(1, len(top_score) + 1)

    # Graph scores
    graph_score = score_df_to_graph(top_score)

    # D3 format
    data = processdata(flower_type, graph_score, num_leaves, config['order'], 0)

    print('len(agg_score)', len(agg_score))

    data['total'] = len(agg_score)

    return flower_type, [data, data.copy(), data.copy()]#, data.copy()] #, node_info


def processdata(gtype, egoG, num_leaves, order, filter_num):
    center_node = egoG.graph['ego']

    # Radius of circle
    radius = 1.2

    # Get basic node information from ego graph
    outer_nodes = list(egoG)
    outer_nodes.remove('ego')

    outer_nodes.sort(key=lambda n: min(-egoG.nodes[n]['inf_out'], -egoG.nodes[n]['inf_in']))

    links = list(egoG.edges(data=True))

    # Sort by name, influence dif, then ratio

    links.sort(key=lambda l: (l[0], l[1]))
    links.sort(key=lambda l: -l[2]['sumw'])

    links_in  = [l for l in links if l[2]['direction'] == 'in']
    links_out = [l for l in links if l[2]['direction'] == 'out']

    # Make sure in/out bars are in order
    links = list()
    for l_in, l_out in zip(links_in, links_out):
        links.append(l_out)
        links.append(l_in)

    if num_leaves > 25:
        anglelist = np.linspace(np.pi*(1+(num_leaves-25)/num_leaves/2), -np.pi*(num_leaves-25)/num_leaves/2, num=len(outer_nodes))
    elif num_leaves < 10:
        anglelist = np.linspace((0.5+num_leaves/20)*np.pi, (0.5-num_leaves/20)*np.pi, num=len(outer_nodes))
    else:
        anglelist = np.linspace(np.pi, 0., num=len(outer_nodes))
    x_pos = [0]; x_pos.extend(list(radius * np.cos(anglelist)))
    y_pos = [0]; y_pos.extend(list(radius * np.sin(anglelist)))

    # Outer nodes data
    nodedata = { key:{
            'name': key,
            'weight': egoG.nodes[key]['nratiow'],
            'id': i,
            'gtype': gtype,
            'size': egoG.nodes[key]['sumw'],
            'sum': egoG.nodes[key]['sum'],
            'xpos': x_pos[i],
            'ypos': y_pos[i],
            'inf_in': egoG.nodes[key]['inf_in'],
            'inf_out': egoG.nodes[key]['inf_out'],
            'dif': egoG.nodes[key]['dif'],
            'ratio': egoG.nodes[key]['ratiow'],
            'coauthor': str(egoG.nodes[key]['coauthor']),
            'bloom_order': egoG.nodes[key]['bloom_order'],
            'filter_num': filter_num,
        } for i, key in zip(range(1, len(outer_nodes)+1), outer_nodes)}

    nodekeys = ['ego'] + [v['name'] for v in sorted(nodedata.values(), key=itemgetter('id'))]

    # Center node data
    nodedata['ego'] = {
        'name': egoG.nodes['ego']['name'],
        'weight': 1,
        'id': 0,
        'gtype': gtype,
        'size': 1,
        'xpos': x_pos[0],
        'ypos': y_pos[0],
        'bloom_order': 0,
        'coauthor': str(False),
        'filter_num': filter_num,
    }

    edge_in = [{
            'source': nodekeys.index(s),
            'target': nodekeys.index(t),
            'padding': nodedata[t]['size'],
            'id': nodedata[t]['id'],
            'gtype': gtype,
            'type': v['direction'],
            'weight': v['nweight'],
            'o_weight': v['weight'],
            'bloom_order': nodedata[t]['bloom_order'],
            'filter_num': filter_num,
        } for s, t, v in links_in]

    edge_out = [{
            'source': nodekeys.index(s),
            'target': nodekeys.index(t),
            'padding': nodedata[t]['size'],
            'id': nodedata[s]['id'],
            'gtype': gtype,
            'type': v['direction'],
            'weight': v['nweight'],
            'o_weight': v['weight'],
            'bloom_order': nodedata[s]['bloom_order'],
            'filter_num': filter_num,
        } for s, t, v in links_out]

    linkdata = list()

    for lin, lout in zip(edge_in, edge_out):
        linkdata.append(lin)
        linkdata.append(lout)

    chartdata = [{
            'id': nodedata[t]['id'] if v['direction'] == 'in' else nodedata[s]['id'],
            'bloom_order': nodedata[t]['bloom_order'] if v['direction'] == 'in' else nodedata[s]['bloom_order'],
            'name': t if v['direction'] == 'in' else s,
            'type': v['direction'],
            'gtype': gtype,
            'sum': nodedata[t]['weight'] if v['direction'] == 'in' else nodedata[s]['weight'],
            'weight': v['weight'],
            'filter_num': filter_num,
        } for s, t, v in links]

    chartdata.sort(key=lambda d: d['bloom_order'])

    return { 'nodes': sorted(list(nodedata.values()), key=itemgetter('id')), 'links': linkdata, 'bars': chartdata }
