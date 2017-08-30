from flask import Flask, jsonify, request
import json


app = Flask(__name__)


## この辺Asset


Assets = [
  {"host":"abccc","lan":"00:00:00:00:00:01","wlan":"10:00:00:00:00:01"},
  {"host":"abcdd","lan":"00:00:00:00:00:02","wlan":"10:00:00:00:00:02"},
  {"host":"acddd","lan":"00:00:00:00:00:03","wlan":"10:00:00:00:00:03"},
  {"host":"acbcc","lan":"00:00:00:00:00:04","wlan":"10:00:00:00:00:04"},
  {"host":"acdda","lan":"00:00:00:00:00:05","wlan":"10:00:00:00:00:05"}
]

@app.route("/Assets/Hosts/")
def getAssetHosts():
    hosts = list(map(lambda i: i['host'],Assets))
    return jsonify(Hosts=hosts)

@app.route("/Assets/Hosts/search/<word>")
@app.errorhandler(404)
def searchAssetHosts(word):
    hosts = list(map(lambda i: i['host'],filter(lambda i:i['host'].find(word)!=-1,Assets)))
    if len(hosts)>0:
        return jsonify(Hosts=hosts)
    return jsonify(msg="{} not match".format(word)), 404

@app.route("/Assets/Host/<name>")
@app.errorhandler(404)
def getAssetHost(name):
    host = list(filter(lambda i:i['host']==name,Assets))
    if len(host) == 1:
        return jsonify(Host=host)
    return jsonify(msg="{} not found".format(name)), 404





































##  この辺から DHCP側

Hosts = [
        {"host":"test","mac":"00:00:00:00:00:01","type":"lan"},
        {"host":"test-a","mac":"00:00:00:00:00:02","type":"lan"},
        {"host":"test-3","mac":"10:00:00:00:00:03","type":"wlan"},
        ]

@app.route("/DHCP/Hosts/")
def getHosts():
    hosts = list(map(lambda i: i['host'],Hosts))
    return jsonify(Hosts=hosts)

@app.route("/DHCP/Hosts/search/<word>")
@app.errorhandler(404)
def searchHosts(word):
    hosts = list(map(lambda m:m['host'],filter(lambda m:m['host'].find(word)!=-1,Hosts)))
    if len(hosts)>0:
        return jsonify(Hosts=hosts)
    return jsonify(msg="{} not match".format(word)), 404

@app.route("/DHCP/Host/<name>",methods=['GET'])
@app.errorhandler(404)
def getHost(name):
    for i in Hosts:
        if i['host']==name:
           return jsonify(i)
    return jsonify(msg="{} not found".format(name)), 404

@app.route("/DHCP/Host/<name>",methods=['PUT'])
@app.errorhandler(406)
def editHost(name):
    data = json.loads(request.data)
    if data['host']!=name:
        return jsonify(msg="name]{} != host]{}".format(name,data['host'])), 406
    for i in Hosts:
        if i['host']==name:
           i['mac']=data['mac']
           i['type']=data['type']
           return jsonify(msg="success",host=i)
    return jsonify(msg="some error")

@app.route("/DHCP/Host/<name>",methods=['POST'])
@app.errorhandler(409)
def createHost(name):
    data = json.loads(request.data)
    if data['host']!=name:
        return jsonify(msg="name != host")
    for i in Hosts:
        if i['host']==name:
           return jsonify(msg="{} is already exist".format(name)), 409
    Hosts.append({"host":data['host'],"mac":data['mac'],"type":data['type']})
    for i in Hosts:
        if i['host']==name:
            return jsonify(msg="success",Host=i)
    return jsonify(msg="some error")

app.run()

