import requests
import json
import hashlib
import sqlite3
from bs4 import BeautifulSoup
import os.path
from os import path
import time
import random
import threading
import os
# import pytesseract
# try:
#     import Image
# except ImportError:
#     from PIL import Image

agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'
        # 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
    # 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G960F Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36',
    # 'Mozilla/5.0 (Linux; Android 7.0; SM-G892A Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/60.0.3112.107 Mobile Safari/537.36',
    # 'Mozilla/5.0 (Linux; Android 7.0; SM-G930VC Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/58.0.3029.83 Mobile Safari/537.36',
    # 'Mozilla/5.0 (Linux; Android 6.0.1; SM-G935S Build/MMB29K; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/55.0.2883.91 Mobile Safari/537.36',
    # 'Mozilla/5.0 (Linux; Android 6.0.1; SM-G920V Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36',
    # 'Mozilla/5.0 (Linux; Android 5.1.1; SM-G928X Build/LMY47X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36',
    # 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 6P Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36',
    # 'Mozilla/5.0 (Linux; Android 7.1.1; G8231 Build/41.2.A.0.219; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36',
    # 'Mozilla/5.0 (Linux; Android 6.0.1; E6653 Build/32.2.A.0.253) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36',
    # 'Mozilla/5.0 (Linux; Android 6.0; HTC One X10 Build/MRA58K; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/61.0.3163.98 Mobile Safari/537.36',
    # 'Mozilla/5.0 (Linux; Android 6.0; HTC One M9 Build/MRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.3',
]

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:83.0) Gecko/20100101 Firefox/83.0',
    'Accept': 'text/html', # ,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.5',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Cookie': 'expandResults=true',
    'DNT': '1',
    'Host': 'www.canlii.org',
    'Pragma': 'no-cache',
    'Referer': 'http://www.canlii.org/en/ca/scc/',
    'TE': 'Trailers',
    'Upgrade-Insecure-Requests': '1'
}

proxies = {
    # 'http': 'http://localhost:8443'
}




def mk_decision(decision):
    """
    Normalize a record into something we'll call a decision. The result should
    have at least the following fields:

    { 'hash': ...
    , 'url':  ...
    , 'name': ...
    }

    """
    decision['hash'] = hashlib.sha1(decision['url']).hexdigest()
    try:
        decision['name'] = decision['styleOfCause']
    except:
        pass
    return decision


class Banned(BaseException):
    pass
class Captcha(BaseException):
    pass
class NoHtml(BaseException):
    pass

def fetch(url):
    hs = headers
    hs['Referer'] = 'http://www.canlii.org' + url
    hs['User-Agent'] = random.choice(agents)
    page = requests.get("http://www.canlii.org" + url, headers=hs, proxies=proxies)
    return page


def get_decision_citations(decision):
    """
    Given a decision, go and fetch the decisions it cites, yielding each.
    """
    page = fetch(decision['url'])
    html = BeautifulSoup(page.content, 'html.parser')

    title = html.find("title")
    if title is None:
        raise NoHtml
    if "Banned" in title.text:
        raise Banned
    if "Captcha" in title.text:
        captcha = html.find("img", id="captchaTag")
        # print ("solved:" + pytesseract.image_to_string(Image.open(requests.get("http://www.canlii.org" + captcha['src'], stream=True).raw)))
        raise Captcha

    # TODO(sandy): does this only find cited? or also citees??
    spans = html.find_all('span', class_='decision')
    for span in spans:
        a = span.find('a', class_='canlii')
        yield mk_decision(
              { 'url': a['href']
              , 'styleOfCause': a.text
              })


def get_scc_year(year):
    """
    Given a year, yield each decision made by the supreme court that year.
    """
    page = requests.get("http://www.canlii.org/en/ca/scc/nav/date/{}/items".format(year))
    decisions = json.loads(page.content)
    for decision in decisions:
        yield mk_decision(decision)


def discover(conn, decision):
    """
    Commit the discovery of a decision to the database.
    """
    try:
        db = conn.cursor()
        db.execute("INSERT INTO decisions(hash, url, name, fetched) VALUES (?, ?, ?, 0)",
                    (decision['hash'], decision['url'], decision['name']))
        conn.commit()
        print( "discovered " + decision['name'])
    except:
        pass


def load_scc_decisions(conn):
    """
    Start the database by discovering every decision made by the SCC.
    """
    for year in range(1877, 2021):
        for decision in get_scc_year(year):
            discover(conn, decision)


def cite(conn, citer, citee):
    """
    Commit that 'citer' cites 'citee' in the database.
    """
    db = conn.cursor()
    db.execute("INSERT INTO citations(citer, citee) VALUES (?, ?)",
                (citer['hash'], citee['hash']))
    conn.commit()
    print( citer['hash'] + " cites " + citee['hash'])


def set_fetched(conn, decision):
    """
    Mark a decision as having been fetched (so we don't go download it again)
    """
    db = conn.cursor()
    db.execute("UPDATE decisions SET fetched = 1 WHERE hash = ?",
                (decision['hash'],))
    conn.commit()
    print( "marking " + decision['hash'] + " as fetched")


# -----------------------------------------------------------

if not (path.exists('canlii.db')):
    conn = sqlite3.connect('canlii.db')
    conn.row_factory = sqlite3.Row

    decisions_table = """
        CREATE TABLE decisions (
          hash CHAR(40) PRIMARY KEY NOT NULL,
          url CHAR(128) NOT NULL,
          name CHAR(256) NOT NULL,
          fetched BOOL NOT NULL
        );
        """

    citations_table = """
        CREATE TABLE citations (
          id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
          citer CHAR(40) NOT NULL,
          citee CHAR(40) NOT NULL,
          FOREIGN KEY(citer) REFERENCES decisions(hash),
          FOREIGN KEY(citee) REFERENCES decisions(hash)
        );
        """

    db = conn.cursor()
    db.execute(decisions_table)
    db.execute(citations_table)
    load_scc_decisions()
else:
    conn = sqlite3.connect('canlii.db')
    conn.row_factory = sqlite3.Row


def fill_discoveries():
    """
    Find discovered decisions which haven't yet been fetched, and go and fetch them.
    """
    conn = sqlite3.connect('canlii.db')
    conn.row_factory = sqlite3.Row
    q = conn.cursor()
    while True:
        q.execute('SELECT * FROM decisions where hash = (SELECT citee FROM (SELECT citee, count (*) AS count FROM citations WHERE citee IN (SELECT hash FROM decisions WHERE url LIKE "%scc%" AND fetched = 0) GROUP BY citee ORDER BY count DESC LIMIT 1));')
        citer = q.fetchone()
        if citer is None:
            return
        try:
            time.sleep(random.uniform(3, 25))
            for citee in get_decision_citations(citer):
                discover(conn, citee)
                cite(conn, citer, citee)
            set_fetched(conn, citer)
        except NoHtml:
            print( "network error")
        except Banned:
            print( "we're banned")
        except Captcha:
            os.system('notify-send "Captcha time" "Go do it yo"')
            os.system('xdg-open "https://www.canlii.org/" &')
            time.sleep(30)

            # raw_input()


def cleanup_after_ban(conn):
    """
    Turns out canlii will ban you if you scrape too hard. This function will
    cleanup the database so we can continue when they unban us.
    """
    db = conn.cursor()
    db.execute("""
        UPDATE decisions
        SET fetched = 0
        WHERE fetched = 1
        AND NOT EXISTS
        (SELECT c.id FROM citations c WHERE c.citer = decisions.hash);
        """);
    conn.commit()


def graphviz():
    """
    Produce a graphviz dot file from the database.
    """
    print( "digraph canlii {")
    conn = sqlite3.connect('canlii.db')
    conn.row_factory = sqlite3.Row
    q = conn.cursor()
    q.execute('select citee from citations union select citer from citations;')
    db = conn.cursor()
    for node in q:
        db.execute('select name from decisions where hash = ?', (node[0],))
        name = db.fetchone()['name']
        print( u'"{}" [label="{}"]'.format(node[0], name.replace('"','\\"')).encode('utf-8'))
    q.execute('SELECT citer, citee FROM citations')
    for node in q:
        print( u'"{}" -> "{}"'.format(node['citer'], node['citee']))
    print ("}")


for i in range(1):
    th = threading.Thread(target=fill_discoveries)
    th.daemon = True
    th.start()

while True:
    time.sleep(1)

