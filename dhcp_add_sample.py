import sqlite3
Hosts = [
    {"host": "test", "mac": "00:00:00:00:00:01",
        "typeid": 1, 'ip': '192.168.1.1'},
    {"host": "test-a", "mac": "00:00:00:00:00:02",
        "typeid": 1, 'ip': '192.168.1.2'},
    {"host": "test-3", "mac": "10:00:00:00:00:03",
        "typeid": 2, 'ip': '192.168.2.3'},
]
Ranges = [
    {"name": "lan", "start": "192.168.1.1", "end": "192.168.1.200", "typeid": 1},
    {"name": "wlan", "start": "192.168.2.1", "end": "192.168.2.200", "typeid": 2},
]

db = sqlite3.connect("server.db")
cur = db.cursor()
for i in Hosts:
    cur.execute("insert into dhcp(host,typeid,mac,ip) values(?,?,?,?);", [
                i['host'], i['typeid'], i['mac'], i['ip']])
for i in Ranges:
    cur.execute("insert into range(name,start,end,typeid) values(?,?,?,?);", [
                i['name'], i['start'], i['end'], i['typeid']])
db.commit()
