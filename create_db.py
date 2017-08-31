import sqlite3
conn = sqlite3.connect('server.db')
c = conn.cursor()

c.executemany(open('schema.sql').read())
c.commit()
c.close()
