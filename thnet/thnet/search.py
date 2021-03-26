from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from operator import itemgetter

ES_SERVER = "localhost:9200"
client = Elasticsearch(ES_SERVER, timeout=600)

def es_search_paper_reference(reflist):
    s = Search(using=client, index="paperreferences")
    s = s.query("terms", _id=reflist)
    response = s.execute()
    result = response.to_dict()["hits"]["total"]
    return result

def es_search_papers_from_aid(authorid):
    s = Search(using=client, index="paperauthoraffiliations")
    s = s.query("match", AuthorId=authorid)
    s = s.params(size=1000)
    response = s.execute()
    result = response.to_dict()["hits"]["hits"]
    data = []
    if result:
        data = [res["_source"]["PaperId"] for res in result]
    else:
        print("[es_search_papers_from_authorid] no result", authorid)
    return data


def es_search_author_id(authorid):
    s = Search(using=client, index="authors")
    s = s.query("match", AuthorId=authorid)
    response = s.execute()
    result = response.to_dict()["hits"]["hits"]
    cols = ["AuthorId", "DisplayName", "NormalizedName", "PaperCount", "CitationCount"]
    if result:
        return r["_source"]
    else:
        print("[es_search_author_id] no result", authorid)
        return None

def es_search_author_name(author_name):
    q = {
        "size": 10,
        "from": 0,
        "query":{
            "function_score": {
                "query": {
                    "bool":{
                        "should": {"match": {"DisplayName": author_name}}
                    }
                },
                "functions": [
                    {"script_score": {
                        "script": "Math.pow(_score, 3) * (Math.log((doc['CitationCount'].value + 10)))"
                    }}
                ]
            }
        }
    }
    s = Search(using=client, index="authors")
    s = s.update_from_dict(q)
    response = s.execute()
    result = response.to_dict()["hits"]["hits"]
    cols = ["AuthorId", "DisplayName", "NormalizedName", "PaperCount", "CitationCount"]
    data = []
    if result:
        data = [r["_source"] for r in result]
        sorted_data = sorted(data, key=itemgetter("PaperCount"), reverse=True)
        return sorted_data[0]
    else:
        print("[es_search_author_name] no result", author_name)
        return []
