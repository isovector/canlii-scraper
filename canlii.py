import requests
import json
import hashlib
import sqlite3
from bs4 import BeautifulSoup
import os.path
from os import path

conn= None
db = None


def mk_decision(decision):
    decision['hash'] = hashlib.sha1(decision['url']).hexdigest()
    try:
        decision['name'] = decision['styleOfCause']
    except:
        pass
    return decision


def load_decision(decision):
    page = requests.get("https://www.canlii.org" + decision['url'])
    html = BeautifulSoup(page.content, 'html.parser')

    h2 = html.find('h2', class_='mainTitle')

    spans = html.find_all('span', class_='decision')
    for span in spans:
        a = span.find('a', class_='canlii')
        yield mk_decision(
              { 'url': a['href']
              , 'styleOfCause': a.text
              })

def get_scc_year(year):
    page = requests.get("https://www.canlii.org/en/ca/scc/nav/date/{}/items".format(year))
    decisions = json.loads(page.content)
    for decision in decisions:
        yield mk_decision(decision)

def discover(decision):
    try:
        db.execute("INSERT INTO decisions(hash, url, name, fetched) VALUES (?, ?, ?, 0)",
                    (decision['hash'], decision['url'], decision['name']))
        conn.commit()
        print "discovered " + decision['name']
    except:
        pass


def load_scc_decisions():
    for year in range(1877, 2021):
        for decision in get_scc_year(year):
            discover(decision)

def cite(citer, citee):
    db.execute("INSERT INTO citations(citer, citee) VALUES (?, ?)",
                (citer['hash'], citee['hash']))
    conn.commit()
    print citer['hash'] + " cites " + citee['hash']

def set_fetched(decision):
    db.execute("UPDATE decisions SET fetched = 1 WHERE hash = ?",
                (decision['hash'],))
    conn.commit()
    print "marking " + decision['hash'] + " as fetched"


# -----------------------------------------------------------

if not (path.exists('canlii.db')):
    print 'creating db'
    conn = sqlite3.connect('canlii.db')
    conn.row_factory = sqlite3.Row
    db = conn.cursor()

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

    db.execute(decisions_table)
    db.execute(citations_table)
    load_scc_decisions()
else:
    conn = sqlite3.connect('canlii.db')
    conn.row_factory = sqlite3.Row
    db = conn.cursor()


def fill_discoveries():
    q = conn.cursor();
    q.execute('SELECT * FROM decisions where fetched=0 ORDER BY hash ASC')

    for citer in q:
        for citee in load_decision(citer):
            discover(citee)
            cite(citer, citee)
        set_fetched(citer)


def cleanup_after_ban():
    db.execute("""
        UPDATE decisions
        SET fetched = 0
        WHERE fetched = 1
        AND NOT EXISTS
        (SELECT c.id FROM citations c WHERE c.citer = decisions.hash);
        """);


def graphviz():
    print "digraph canlii {"
    q = conn.cursor()
    q.execute('SELECT hash, name FROM decisions')
    for node in q:
        print u'"{}" [label="{}"]'.format(node['hash'], node['name'].replace('"','\\"')).encode('utf-8')
    q.execute('SELECT citer, citee FROM citations')
    for node in q:
        print u'"{}" -> "{}"'.format(node['citer'], node['citee'])
    print "}"

fill_discoveries()
