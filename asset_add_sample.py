import sqlite3
Assets = [
    {"host": "abccc", "lan": "00:00:00:00:00:01", "wlan": "10:00:00:00:00:01"},
    {"host": "abcdd", "lan": "00:00:00:00:00:02", "wlan": "10:00:00:00:00:02"},
    {"host": "acddd", "lan": "00:00:00:00:00:03", "wlan": "10:00:00:00:00:03"},
    {"host": "acbcc", "lan": "00:00:00:00:00:04", "wlan": "10:00:00:00:00:04"},
    {"host": "acdda", "lan": "00:00:00:00:00:05", "wlan": "10:00:00:00:00:05"}
]


db = sqlite3.connect("server.db")
cur = db.cursor()


for i in Assets:
    cur.execute("insert into asset values(?,?,?) ;",
                [i['host'], i['lan'], i['wlan']])
# cur.commit()
db.commit()
