import os, json, csv
from itertools import product, permutations
from operator import itemgetter
from collections import Counter
from .network import clean, born_year, create_school_map

def convert_to_csv():
    data = json.load(open("data/philosophers_MAG.json", "r"))
    data = clean(data)

    csvfile = open('philosophers_MAG.csv', 'w', newline='')
    spamwriter = csv.writer(csvfile)
    for i, p in enumerate(data):
        pid = p["pageid"]
        ptime = born_year(p["born"]) if p["born"] else 0
        pname = p["name"] if p["name"] else ""

        MAG_id = MAG_name = "no info"
        MAG_pcount = MAG_ccount = 0
        if "MAG_id" in p:
            MAG_id = p["MAG_id"]
            MAG_name = p["MAG_name"]
            MAG_pcount = p["MAG_pcount"]
            MAG_ccount = p["MAG_ccount"]
        spamwriter.writerow([pid, pname, ptime, MAG_id, MAG_name, MAG_pcount, MAG_ccount])
