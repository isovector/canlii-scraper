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


def load_decision(decision):
    """
    Given a decision, go and fetch the decisions it cites, yielding each.
    """
    page = requests.get("https://www.canlii.org" + decision['url'])
    html = BeautifulSoup(page.content, 'html.parser')

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
    page = requests.get("https://www.canlii.org/en/ca/scc/nav/date/{}/items".format(year))
    decisions = json.loads(page.content)
    for decision in decisions:
        yield mk_decision(decision)


def discover(decision):
    """
    Commit the discovery of a decision to the database.
    """
    try:
        db.execute("INSERT INTO decisions(hash, url, name, fetched) VALUES (?, ?, ?, 0)",
                    (decision['hash'], decision['url'], decision['name']))
        conn.commit()
        print "discovered " + decision['name']
    except:
        pass


def load_scc_decisions():
    """
    Start the database by discovering every decision made by the SCC.
    """
    for year in range(1877, 2021):
        for decision in get_scc_year(year):
            discover(decision)


def cite(citer, citee):
    """
    Commit that 'citer' cites 'citee' in the database.
    """
    db.execute("INSERT INTO citations(citer, citee) VALUES (?, ?)",
                (citer['hash'], citee['hash']))
    conn.commit()
    print citer['hash'] + " cites " + citee['hash']


def set_fetched(decision):
    """
    Mark a decision as having been fetched (so we don't go download it again)
    """
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
    """
    Find discovered decisions which haven't yet been fetched, and go and fetch them.
    """
    q = conn.cursor();
    q.execute('SELECT * FROM decisions where fetched=0 ORDER BY hash ASC')

    # TODO(sandy): bug here; it won't fetch anything that was discovered as
    # part of ths loop
    for citer in q:
        for citee in load_decision(citer):
            discover(citee)
            cite(citer, citee)
        set_fetched(citer)


def cleanup_after_ban():
    """
    Turns out canlii will ban you if you scrape too hard. This function will
    cleanup the database so we can continue when they unban us.
    """
    db.execute("""
        UPDATE decisions
        SET fetched = 0
        WHERE fetched = 1
        AND NOT EXISTS
        (SELECT c.id FROM citations c WHERE c.citer = decisions.hash);
        """);


def graphviz():
    """
    Produce a graphviz dot file from the database.
    """
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

