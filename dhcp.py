# -*- coding: utf-8 -*-
import os
import sqlite3
from flask import Flask, jsonify, request, g
import json

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, "server.db")
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
                 'host': i['host'], 'mac': i['mac'], 'type': i['type'], 'ip': i['ip']}, data))
    return jsonify(Hosts=hosts)


@app.route("/DHCP/Hosts/search/<word>")
@app.errorhandler(404)
def searchHosts(word):
    db = get_db()
    cur = db.execute("select * from dhcp where host like ?;",
                     ['%' + word + '%'])
    data = cur.fetchall()
    hosts = list(map(lambda i: {
                 'host': i['host'], 'mac': i['mac'], 'type': i['type'], 'ip': i['ip']}, data))
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
    data = json.loads(request.data)
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
    data = json.loads(request.data)
    if data['host'] != name:
        return jsonify(msg="name != host")
    db = get_db()
    cur = db.execute("select host from dhcp where host == ?;", [name])
    if not cur.fetchone():
        return jsonify(msg="{} is not found".format(name))
    cur = db.execute("delete from dhcp where host == ? and mac == ? and ip == ?;", [
                     name, data['mac'], data['ip']])
    cur = db.execute("select host from dhcp where host == ?;", [name])
    if cur.fetchone():
        return jsonify(msg="some error")
    db.commit()
    return jsonify(msg="success", host=data)


@app.route("/DHCP/Host/<name>", methods=['POST'])
@app.errorhandler(409)
def createHost(name):
    data = json.loads(request.data)
    if data['host'] != name:
        return jsonify(msg="name != host")
    db = get_db()
    cur = db.execute("select host from dhcp where host == ?;", [name])
    if cur.fetchone():
        return jsonify(msg="{} is already exist".format(name)), 409
    ip = _getIP(data['type'])
    cur = db.execute("insert into dhcp values(?,?,?,?);", [
                     data['host'], data['type'], data['mac'], ip])
    db.commit()
    cur = db.execute("select * from dhcp where host == ?;", [name])
    data = cur.fetchone()
    if data:
        return jsonify(msg="success", Host={"host": data['host'], "mac": data['mac'], "type": data['type'], "ip": data['ip']})
    return jsonify(msg="some error")


def _getIP(type):
    db = get_db()
    cur = db.execute("select ip from dhcp;")
    data = cur.fetchall()
    data = map(lambda i: i['ip'], data)
    if type == "lan":
        prefix = "192.168.1."
    elif type == "wlan":
        prefix = "192.168.2."
    else:
        return None
    for i in range(1, 50):
        ip = prefix + str(i)
        if not ip in data:
            return ip
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


if __name__ == "__main__":
    app.run('0.0.0.0')
