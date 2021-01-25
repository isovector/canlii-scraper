import sqlite3

conn = sqlite3.connect('canlii2.db')
conn.row_factory = sqlite3.Row


def alter(conn):
    db = conn.cursor()
    conn.execute('alter table decisions add column jurisdiction CHAR(2);')
    conn.execute('alter table decisions add column court CHAR(8);')
    conn.execute('alter table decisions add column year INT;')
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

        db.execute('update decisions set jurisdiction = ?, court = ?, year = ? where hash = ?', (jurisdiction, court, year, row['hash']));

        print (jurisdiction, court, year)

    conn.commit()

