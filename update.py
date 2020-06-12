import datetime

from bs4 import BeautifulSoup
import requests
import json

DISCUSS_URL = "https://news.ycombinator.com/item?id="

def get_info(soup):
    ret = []
    d = {}
    text = soup.get_text()
    text = text[text.find("1."):text.find("\nMore\n")]
    text = text.split("\n")[1::4]

    for line in text:
        if " hide " in line:
            line = line.replace(" | hide | ", "| ", 1).replace("\xa0", " ", 1).strip()

        d['info_str'] = line

        has_points = 1 if "point" in line else 0
        has_comment = 1 if "comment" in line else 0
        has_author = 1 if " by " in line else 0
        has_ts = 1 if " ago " in line else 0


        line = line.split()
        posted_idx = line.index("ago")

        d['points'] = line[0] if has_points else ""
        d['nb_comments'] = line[-2] if has_comment else 0
        d['author'] = line[3] if has_author else ""
        d['posted_at'] = " ".join(line[posted_idx - 2:posted_idx + 1])
        ret.append(d)
        del d
        d = {}

    return ret


def get_ids(soup):
    ids = []
    for el in soup.select('a[href*="hide"]'): # middle match
        if "hide" in el.text:
            href = el['href']
            start = href.find("=") + 1
            end = start + 8
            ids.append(href[start:end])
    return ids


def get_info_dicts(url = 'https://news.ycombinator.com/', page = ''):
    if page:
        url = url + 'news?p=' + str(page)
    re = requests.get(url).text
    soup = BeautifulSoup(re, 'html.parser')

    info_dicts = get_info(soup)
    ids = get_ids(soup)
    links = soup.findAll("a", {"class": "storylink"})
    i = 0
    current_time = str(datetime.datetime.now().time()).split('.')[0]
    for d, sid, link in zip(info_dicts, ids, links):
        info_dicts[i]['title'] = link.text
        info_dicts[i]['href'] = link['href'] if "http" in link['href'] else DISCUSS_URL + sid
        info_dicts[i]['id'] = sid
        info_dicts[i]['discussion_url'] = DISCUSS_URL + sid
        info_dicts[i]['added_ts'] = current_time
        info_dicts[i]['on_front'] = 'True' if page == 1 else "False"
        i += 1
    return info_dicts

sort_f = lambda k: max(int(k['points']) * int(k['nb_comments']), int(k['points']))
front_page_dicts = []
for i in range(1, 4):
    front_page_dicts += get_info_dicts(page = i)
all_sorted = sorted(front_page_dicts, key=sort_f, reverse = True)
info_dicts = all_sorted

#with open("./new.css", "r") as f:
#    css_script = f.read()

strTable = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>hn archiver demo</title>
    <meta name="description" content="Here you can view the all the links that were on a front page of hn today">
    <meta name="keywords" content="hn,hackernews,project,news,links">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@exampledev/new.css@1/new.min.css">
    <link rel="stylesheet" href="https://fonts.xz.style/serve/inter.css">
</head>
<body>
<table><tr><th>Score</th><th>Article</th><th>comments</th></tr>
"""
#<th>seen at</th>
#<link rel="stylesheet" href="new.css">
#<style>{css_script}</style>

#     <link rel="stylesheet" href="new.css">
def a(href, text, blank=True):
    if blank:
        return f"""<a href="{href}" target="_blank">{text}</a>"""
    else:
        return f"""<a href="{href}">{text}</a>"""
bg = ""
for i, d in enumerate(info_dicts):
    title = d['title']
    href = d['href']
    nb_comments = d['nb_comments']
    du = d['discussion_url']
    # points = str(max(int(d['points']) * int(d['nb_comments']), 0)) 
    points = d['points']

    # cur_hour = str(datetime.datetime.now().hour)
    bg = """ style="background-color: #fcfc7e\"""" if d['on_front'] == 'True' else ""
    added_td = f"<td>{d['added_ts'][:-3]}</td>" 
    added_td = ""
    strRW = f"""<tr {bg}><td>{points}</td><td>{a(href, title)}<td>{a(du, f"{nb_comments}")}</td>{added_td}</tr>"""
    strTable = strTable+strRW + "\n"

strTable = strTable+"</table></body></html>"
 
with open("index.html", 'w') as hs:
    hs.write(strTable)
