from flask import Flask,request,jsonify,Response
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson import json_util
import json
import math as m
import queue

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost/gbfs'
CORS(app)

mongo = PyMongo(app)

def getheuristic(goalNode):
    heuristics = {}
    cities = getcity()
    response = json_util.dumps(cities)
    iterator = json.loads(response)

    for client in iterator:
        if (goalNode in client['name']):
            latitud = client['latitud']
            longitud = client['longitud']

    for client in iterator:
        name = client['name']
        distancia = m.sqrt(m.pow((client['latitud'] - latitud), 2) + m.pow((client['longitud'] - longitud), 2))
        heuristics[name] = distancia

    return heuristics

def setcities(path):
    cities = getcity()
    response = json_util.dumps(cities)
    iterator = json.loads(response)
    data = []

    for client in iterator:
        for i in path:
            if i in client['name']:
                client['type'] = 'E'
        data.append(client)

    return data

def setgraph(path):
    cities = getgrhaps()
    response = json_util.dumps(cities)
    iterator = json.loads(response)
    data = []
    a = 0

    for client in iterator:
        while a < len(path):
            if a < len(path) - 1:
                if (path[a] == client['city_1'] and path[a + 1] == client['city_2']) or (path[a]  == client['city_2'] and path[a + 1] == client['city_1']):
                    client['color'] = 'blue'
            a = a + 1
        a = 0
        data.append(client)

    return data

def getrute(path):
    data = []
    a = 0

    while a < len(path):
        if a < len(path) - 1:
            obj = {
                'city_00': path[a],
                'city_01': path[a+1]
            }
            data.append(obj)
        a = a + 1

    return data

def createGraphs():
    graph = {}
    cities = getgrhaps()
    response = json_util.dumps(cities)
    iterator = json.loads(response)
    for client in iterator:
        node_val = client

        if node_val['city_1'] in graph and node_val['city_2'] in graph:
            c = graph.get(node_val['city_1'])
            c.append([node_val['city_2'], node_val['distancia']])
            graph.update({node_val['city_1']: c})

            c = graph.get(node_val['city_2'])
            c.append([node_val['city_1'], node_val['distancia']])
            graph.update({node_val['city_2']: c})

        elif node_val['city_1'] in graph:
            c = graph.get(node_val['city_1'])
            c.append([node_val['city_2'], node_val['distancia']])
            graph.update({node_val['city_1']: c})

            graph[node_val['city_2']] = [[node_val['city_1'], node_val['distancia']]]

        elif node_val['city_2'] in graph:
            c = graph.get(node_val['city_2'])
            c.append([node_val['city_1'], node_val['distancia']])
            graph.update({node_val['city_2']: c})

            graph[node_val['city_1']] = [[node_val['city_2'], node_val['distancia']]]

        else:
            graph[node_val['city_1']] = [[node_val['city_2'], node_val['distancia']]]
            graph[node_val['city_2']] = [[node_val['city_1'], node_val['distancia']]]

    return graph

def GBFS(startNode, heuristics, graph, goalNode):
    priorityQueue = queue.PriorityQueue()
    priorityQueue.put((heuristics[startNode], startNode))
    path = []

    while priorityQueue.empty() == False:
        current = priorityQueue.get()[1]
        path.append(current)

        if current == goalNode:
            break

        priorityQueue = queue.PriorityQueue()

        for i in graph[current]:
            if i[0] not in path:
                priorityQueue.put((heuristics[i[0]], i[0]))

    return path


def getcity():
    return mongo.db.city.find()

def getgrhaps():
    return mongo.db.graph.find()

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

@app.route('/createcity')
def crete_city():  # put application's code here
    fileName = 'PiuraCiudades.json'

    with open(fileName) as file:
        data = json.load(file)
        for client in data:
            if (client['Tipo'] == 'Principal'):
                tipo = 'P'
            else:
                tipo = 'I'
            ciudad = client['Ciudad']
            latitud = client['Latitud']
            longitud = client['Longitud']
            id = mongo.db.city.insert(
                {
                    'name': ciudad,
                    'latitud': latitud,
                    'longitud': longitud,
                    'type': tipo,
                }
            )
            response = {
                'id': str(id),
                'ciudad': ciudad
            }

    return response

@app.route('/createpoints')
def crete_points():  # put application's code here
    fileName = 'PuntosCiudades.json'

    with open(fileName) as file:
        data = json.load(file)
        for client in data:
            ciudad_1 = client['Ciudad_1']
            latitud_1 = client['Latitud_1']
            longitud_1 = client['Longitud_1']
            ciudad_2 = client['Ciudad_2']
            latitud_2 = client['Latitud_2']
            longitud_2 = client['Longitud_2']
            distancia = client['Distancia']
            color = 'black'
            id = mongo.db.graph.insert(
                {
                    'city_1': ciudad_1,
                    'latitud_1': latitud_1,
                    'longitud_1': longitud_1,
                    'city_2': ciudad_2,
                    'latitud_2': latitud_2,
                    'longitud_2': longitud_2,
                    'distancia': distancia,
                    'color': color
                }
            )
            response = {
                'id': str(id),
                'ciudad_1': ciudad_1,
                'ciudad_2': ciudad_2
            }

    return response

@app.route('/getcity')
def get_city():
    cities = getcity()
    response = json_util.dumps(cities)
    return Response(response, mimetype='application/json')

@app.route('/getgrhaps')
def get_grhaps():
    grhaps = getgrhaps()
    response = json_util.dumps(grhaps)
    return Response(response, mimetype='application/json')

@app.route('/generateroute', methods=['POST'])
def generate_route():
    goalNode = request.json['destino']
    startNode = request.json['origen']
    heuristics = getheuristic(goalNode)
    graph = createGraphs()
    response = json_util.dumps(GBFS(startNode,heuristics,graph,goalNode))
    return Response(response, mimetype='application/json')

@app.route('/getroute', methods=['POST'])
def geting_route():
    goalNode = request.json['destino']
    startNode = request.json['origen']
    heuristics = getheuristic(goalNode)
    graph = createGraphs()
    get = getrute(GBFS(startNode,heuristics,graph,goalNode))
    response = json_util.dumps(get)
    return Response(response, mimetype='application/json')

@app.route('/setcity', methods=['POST'])
def set_city():
    goalNode = request.json['destino']
    startNode = request.json['origen']
    heuristics = getheuristic(goalNode)
    graph = createGraphs()
    set = setcities(GBFS(startNode,heuristics,graph,goalNode))
    response = json_util.dumps(set)
    return Response(response, mimetype='application/json')

@app.route('/setgraph', methods=['POST'])
def set_graph():
    goalNode = request.json['destino']
    startNode = request.json['origen']
    heuristics = getheuristic(goalNode)
    graph = createGraphs()
    set = setgraph(GBFS(startNode,heuristics,graph,goalNode))
    response = json_util.dumps(set)
    return Response(response, mimetype='application/json')

@app.errorhandler(404)
def not_found(error=None):
    response = jsonify({
        'mesage': 'Resource Not Found: ' + request.url,
        'status': 404
    })
    response.status_code = 404
    return response

if __name__ == '__main__':
    app.run(debug=True)
