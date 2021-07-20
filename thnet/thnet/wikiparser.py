import urllib.request
from bs4 import BeautifulSoup

def parse_page(url):
    print("parse_page", url)
    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')
    name = soup.find("h1", {"id": "firstHeading"}).get_text()
    biography = soup.find("table", {"class":"infobox biography vcard"})

    columns = ["Born", "Died", "Alma\xa0mater", "Era"]
    basic_info = {}

    if biography:
        basic_info = {tr.th.get_text():str(tr.td) for tr in biography.find_all("tr")\
                    if tr.find("th") and tr.th.get_text() in columns}
    data = {
        "title": name,
        "basic_info": basic_info
    }
    # print(data)
    return data
