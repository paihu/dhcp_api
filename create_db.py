import sqlite3
conn = sqlite3.connect('server.db')
c = conn.cursor()

c.executescript(open('schema.sql').read())
conn.commit()
conn.close()
