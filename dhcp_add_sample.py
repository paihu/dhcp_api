import sqlite3
Hosts = [
    {"host": "test", "mac": "00:00:00:00:00:01",
        "type": "lan", 'ip': '192.168.1.1'},
    {"host": "test-a", "mac": "00:00:00:00:00:02",
        "type": "lan", 'ip': '192.168.1.2'},
    {"host": "test-3", "mac": "10:00:00:00:00:03",
        "type": "wlan", 'ip': '192.168.1.3'},
]


db = sqlite3.connect("server.db")
cur = db.cursor()
for i in Hosts:
    cur.execute("insert into dhcp values(?,?,?,?);", [
                i['host'], i['type'], i['mac'], i['ip']])
db.commit()
