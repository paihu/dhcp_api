# -*- coding: utf-8 -*-
import os
import sqlite3
from flask import Flask, jsonify, request, g
import json
from jinja2 import Template, Environment, PackageLoader

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, "server.db"),
    DIR=os.path.join(app.root_path,"static")
))
app.config.from_envvar('DHCP_SETTINGS', silent=True)
# この辺Asset


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    init_db()
    print("initialized the database")


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route("/Assets/Hosts/")
def getAssetHosts():
    db = get_db()
    cur = db.execute("select * from asset;")

    data = cur.fetchall()
    hosts = []
    for i in data:
        hosts.append({'host': i['host'], 'lan': i['lan'], 'wlan': i['wlan']})
    return jsonify(Hosts=hosts)


@app.route("/Assets/Hosts/search/<word>")
@app.errorhandler(404)
def searchAssetHosts(word):
    db = get_db()
    cur = db.execute("select host from asset where host like ?;", [
                     '%' + word + '%'])
    data = cur.fetchall()
    hosts = []
    for i in data:
        hosts.append(i['host'])

    if len(hosts) > 0:
        return jsonify(Hosts=hosts)
    return jsonify(msg="{} not match".format(word)), 404


@app.route("/Assets/Host/<name>")
@app.errorhandler(404)
def getAssetHost(name):
    db = get_db()
    cur = db.execute("select * from asset where host = ?;", [name])
    data = cur.fetchone()
    if data == None:
        return jsonify(msg="{} not found".format(name)), 404
    host = {"host": data["host"], "lan": data["lan"], "wlan": data["wlan"]}
    return jsonify(Host=host)


# この辺から DHCP側

@app.route("/DHCP/Hosts/")
def getHosts():
    db = get_db()
    cur = db.execute("select * from dhcp;")
    data = cur.fetchall()
    hosts = list(map(lambda i: {
                 'host': i['host'], 'mac': i['mac'], 'type': i['typeid'], 'ip': i['ip']}, data))
    return jsonify(Hosts=hosts)


@app.route("/DHCP/Hosts/Macsearch/<word>")
@app.errorhandler(404)
def searchHostsfromMac(word):
    db = get_db()
    cur = db.execute("select * from dhcp where mac like ?;",
                     ['%' + word + '%'])
    data = cur.fetchall()
    hosts = list(map(lambda i: {
                 'host': i['host'], 'mac': i['mac'], 'type': i['typeid'], 'ip': i['ip']}, data))
    if len(hosts) > 0:
        return jsonify(Hosts=hosts)
    return jsonify(msg="{} not match".format(word)), 404

@app.route("/DHCP/Hosts/search/<word>")
@app.errorhandler(404)
def searchHosts(word):
    db = get_db()
    cur = db.execute("select * from dhcp where host like ?;",
                     ['%' + word + '%'])
    data = cur.fetchall()
    hosts = list(map(lambda i: {
                 'host': i['host'], 'mac': i['mac'], 'type': i['typeid'], 'ip': i['ip']}, data))
    if len(hosts) > 0:
        return jsonify(Hosts=hosts)
    return jsonify(msg="{} not match".format(word)), 404


@app.route("/DHCP/Host/<name>", methods=['GET'])
@app.errorhandler(404)
def getHost(name):
    db = get_db()
    cur = db.execute("select * from dhcp where host = ?;", [name])
    data = cur.fetchone()
    if data:
        return jsonify(Host={'host': data['host'], 'mac': data['mac'], 'type': data['type'], 'ip': data['ip']})
    return jsonify(msg="{} not found".format(name)), 404


@app.route("/DHCP/Host/<name>", methods=['PUT'])
@app.errorhandler(406)
def editHost(name):
    data = json.loads(request.data.decode('utf-8'))
    if data['host'] != name:
        return jsonify(msg="name]{} != host]{}".format(name, data['host'])), 406
    db = get_db()
    cur = db.execute("select host from dhcp where host == ?;", [name])
    if not cur.fetchone():
        return jsonify(msg="{} is not found".format(name))
    cur = db.execute("update values(?,?,?,?) from dhcp where host== ?;", [
                     name, data['type'], data['mac'], data['ip'], name])
    if not cur:
        return jsonify(msg="success", host=i)
    return jsonify(msg="some error")


@app.route("/DHCP/Host/<name>", methods=['DELETE'])
@app.errorhandler(406)
def deleteHost(name):
    db = get_db()
    cur = db.execute("select host from dhcp where host == ?;", [name])
    if not cur.fetchone():
        return jsonify(msg="{} is not found".format(name))
    cur = db.execute("delete from dhcp where host == ? ;", [
                     name])
    cur = db.execute("select host from dhcp where host == ?;", [name])
    if cur.fetchone():
        return jsonify(msg="some error")
    db.commit()
    generateConf()
    return jsonify(msg="{} delete success".format(name))


@app.route("/DHCP/Host/<name>", methods=['POST'])
@app.errorhandler(409)
def createHost(name):
    data = json.loads(request.data.decode('utf-8'))
    app.logger.error(data)
    if data['host'] != name:
        return jsonify(msg="name != host")
    db = get_db()
    cur = db.execute("select host from dhcp where host == ?;", [name])
    if cur.fetchone():
        return jsonify(msg="{} is already exist".format(name)), 409
    ip = _getIP(data['typeid'])
    app.logger.error(ip)
    try:
        cur = db.execute("insert into dhcp values(?,?,?,?);", [
                     data['host'], data['typeid'], data['mac'], ip])
    except Exception as e:
        return jsonify(msg=str(e))
    db.commit()
    generateConf()
    cur = db.execute("select * from dhcp where host == ?;", [name])
    data = cur.fetchone()
    if data:
        return jsonify(msg="success", Host={"host": data['host'], "mac": data['mac'], "typeid": data['typeid'], "ip": data['ip']})
    return jsonify(msg="some error")


def _strip_to_intip(s):
    d = [int(x) for x in s.split(".")]
    return (d[0]<<24)+(d[1]<<16)+(d[2]<<8)+d[3]

def _intip_to_strip(i):
    d4 = i & 0b11111111
    d3 = (i >> 8) & 0b11111111
    d2 = (i >> 16) & 0b11111111
    d1 = (i >> 24) & 0b11111111
    return str(d1)+"."+str(d2)+"."+str(d3)+"."+str(d4)
    
def _getIP(typeid):
    db = get_db()
    cur = db.execute("select start,end from range where typeid = ?;",[typeid])
    dhcp_range = cur.fetchone()
    dhcp_start = _strip_to_intip(dhcp_range['start'])
    dhcp_end = _strip_to_intip(dhcp_range['end'])
    cur = db.execute("select ip from dhcp where typeid = ? ;",[typeid])
    data = cur.fetchall()
    used = sorted([_strip_to_intip(x['ip']) for x in data])
    if not used:
        return _intip_to_strip(dhcp_start)
    app.logger.error(dhcp_start)
    app.logger.error(dhcp_end)
    for i,v in enumerate(used):
        if(v >= dhcp_start and v < dhcp_end):
            app.logger.error(v)
            if(i != len(used)-1 and v+1 != used[i+1]):
                return _intip_to_strip(v+1)
            if(i != 0 and v-1 != used[i-1]):
                return _intip_to_strip(v-1)
            if(i == len(used)-1 and v < dhcp_end ):
                return _intip_to_strip(v+1)
    return None


@app.route("/DHCP/IP/<type>", methods=['GET'])
@app.errorhandler(404)
def getIP(type):
    db = get_db()
    cur = db.execute("select ip from dhcp;")
    data = cur.fetchall()
    data = map(lambda i: i['ip'], data)
    if type == "lan":
        prefix = "192.168.1."
    elif type == "wlan":
        prefix = "192.168.2."
    else:
        return jsonify(msg="not found"), 404
    for i in range(1, 50):
        ip = prefix + str(i)
        if not ip in data:
            return jsonify(IP=ip)
    return jsonify(msg="not found"), 404

@app.route("/DHCP/RANGE/", methods=['GET'])
@app.errorhandler(404)
def getRanges():
    db = get_db()
    cur = db.execute("select * from range;")
    data = cur.fetchall()
    dataobj = []
    for d in data:
        dataobj.append({"name": d["name"],"start": d["start"], "end": d["end"], "typeid": d["typeid"]})
    return jsonify(Ranges=dataobj)

@app.route("/DHCP/RANGE/<id>", methods=['GET'])
@app.errorhandler(404)
def getRange(id):
    if(not int(id)):
        return jsonify(msg="not found"), 404
    db = get_db()
    cur = db.execute("select * from range where typeid = ?;",[id])
    data = cur.fetchone()
    if(not data):
        return jsonify(msg="not found"), 404
    return jsonify({"name":data["name"],"start": data["start"], "end": data["end"], "typeid": data["typeid"]})

@app.route("/DHCP/RANGE/<name>", methods=['POST'])
@app.errorhandler(404)
@app.errorhandler(409)
def createRange(name):
    try:
        data = json.loads(request.data.decode('utf-8'))
    except Exception as e:
        app.logger.error(request)
        app.logger.error(request.data)
        app.logger.error(e)
        return jsonify(msg="param not found"), 404
    if(not 'start' in data) or (not 'end' in data) or (not 'name' in data):
        return jsonify(msg="param not found"), 404

    db = get_db()
    cur = db.execute("select id from range where start = ?;",[data["start"]])
    if(not cur.fetchone()):
        return jsonify(msg="range is alreay defined")
    cur = db.execute("select id from range where end = ?;",[data["end"]])
    if(not cur.fetchone()):
        return jsonify(msg="range is alreay defined")
    cur = db.execute("select id from range where name = ?;",[data["name"]])
    if(not cur.fetchone()):
        return jsonify(msg="range is alreay defined")
    cur = db.execute("insert into range(start,end,name) values(?,?,?);",[data["start"],data["end"],data["name"]])
    cur = db.execute("select * from range where name = ?;",[data["name"]])
    ret = cur.fetchone()
    if(not ret):
        return jsonify(msg="some error"), 404
    return jsonify(name=ret["name"],start=ret["start"],end=ret["end"],id=ret['id'])

def generateConf():
    env = Environment(
    loader = PackageLoader("dhcp","template")
    )
    template = env.get_template('host.tpl')
    #print(template.render(hosts=[{'host':'test','ip':'10.0.0.1','mac':'00:00:00:00:00:01'}]))
    db = get_db()
    cur = db.execute("select typeid from dhcp")
    rows = cur.fetchall()
    types=[]
    for row in rows:
        types.append(row['typeid'])
    types = set(types)
    for t in types:
        cur = db.execute("select host,mac,ip from dhcp where typeid=?" , (t,))
        rows = cur.fetchall()
        with open(os.path.join(app.config['DIR'],str(t)+".txt"),"w") as f:
            f.write(template.render(hosts=rows))
    


if __name__ == "__main__":
    app.run('0.0.0.0')
