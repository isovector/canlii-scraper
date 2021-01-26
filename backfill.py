import sqlite3

conn = sqlite3.connect('canlii2.db')
conn.row_factory = sqlite3.Row


def alter(conn):
    db = conn.cursor()
    conn.execute('alter table decisions add column jurisdiction CHAR(2);')
    conn.execute('alter table decisions add column court CHAR(8);')
    conn.execute('alter table decisions add column year INT;')
    conn.execute('alter table decisions add column decade INT;')
    conn.execute('alter table decisions add column decade_rank INT;')
    conn.commit()



def backfill(conn):
    db = conn.cursor()

    q = conn.cursor()
    q.execute('select hash, url from decisions where year is null;')

    for row in q:
        bits = row['url'].split('/')
        jurisdiction = bits[2]
        court = bits[3]
        year = bits[5]
        decade = int(year) / 10 * 10

        db.execute('update decisions set jurisdiction = ?, court = ?, year = ?, decade = ? where hash = ?', (jurisdiction, court, year, decade, row['hash']));

        print (jurisdiction, court, year)

    conn.commit()

def cleanup(conn):
    db = conn.cursor()
    db.execute('update decisions set year = 1951, decade = 1950 where hash = "ada4c5ad7435e34298b5a14290227ccab5bc67fc"')
    conn.commit()


def normalize_decade(conn):
    q = conn.cursor()
    q.execute('select decade from decisions order by decade asc limit 1;')
    smallest = q.fetchone()
    q.execute('update decisions set decade_rank = (decade - ?) / 10', (smallest['decade'],))
    conn.commit()


# alter(conn)
# backfill(conn)
cleanup(conn)
normalize_decade(conn)

