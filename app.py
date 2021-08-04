# Blockchain Yeison Prieto
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse


# Paso 1 armar Blockchain

class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions =[]
        self.create_block(proof =1, previous_hash='0')
        self.nodes = set()

    #Añadir nodo al blockchain
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and  self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
            if longest_chain:
                self.chain = longest_chain
                return True
        return False


    #Se define nuevo bloque minado
    def create_block(self,proof, previous_hash):
        # se añaden parametros al bloque en caso de requerirlo ( se puede pasar un parametro en caso de ser necesario)
        block = {
            'index':len(self.chain)+1,
            'timestamp':str(datetime.datetime.now()),
            'proof':proof,
            'previous_hash':previous_hash,
            'transactions':self.transactions
                 }
        self.transactions = []
        self.chain.append(block)
        return block

    #Se añaden transacciones
    def add_transaction(self, biologic, dosis, vaccinationDate,producer,lote,vaccinatorName,vaccinatorId,name,phone,id,mail):
        self.transactions.append({'biologic':biologic,'dosis':dosis,'vaccinationDate':vaccinationDate,'producer':producer,'lote':lote})
        self.transactions.append({'vaccinatorName': vaccinatorName, 'vaccinatorId': vaccinatorId})
        self.transactions.append({'name': name, 'phone': phone,'id':id,'mail':mail})
        previous_block = self.get_previous_block()
        return previous_block['index']+1

    #obtener bloque anterior
    def get_previous_block(self):
        return self.chain[-1]

    #Se define problema dificil de resolver y facil de verificar para que los mineros puedan resolver
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    #se obtiene el hash del bloque
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    # se valida que el proof sea valido según lo definido hash_operation[:4] == '0000' empieza con 4 ceros
    # y el previus hash sea correcto
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

# paso 2 - Se crea servicio REST para poder minar los bloques
app = Flask(__name__)

#crear UUID como dirección del nodo
node_address = str(uuid4()).replace('-','')

blockchain = Blockchain()

# Minando un nuevo bloque
@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    #blockchain.add_transaction(sender= node_address, receiver='chain', amount=1)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message':'Haz minado un bloque!',
                'index':block['index'],
                'timestamp':block['timestamp'],
                'proof':block['proof'],
                'previous_hash':block['previous_hash'],
                'transactions':block['transactions']}
    return jsonify(response),200

# Obteniendo cadena completa
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain':blockchain.chain,
                'length':len(blockchain.chain)}
    return jsonify(response),200

#validez cadena de bloques
@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message':'Blockchain es valido'}
    else:
        response = {'message': 'Blockchain NO es valido'}
    return jsonify(response), 200


# Agregando nueva transaccion al blockchain
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = [
        'biologic',
        'dosis',
        'vaccinationDate',
        'producer',
        'lote',
        'vaccinatorName',
        'vaccinatorId',
        'name',
        'phone',
        'id',
        'mail']
    if not all(key in json for key in transaction_keys):
        return 'Algun elemento de la transaccion esta faltando', 400

    index = blockchain.add_transaction(
        json['biologic'],
        json['dosis'],
        json['vaccinationDate'],
        json['producer'],
        json['lote'],
        json['vaccinatorName'],
        json['vaccinatorId'],
        json['name'],
        hashlib.sha256(str(json['phone']).encode()).hexdigest(),
        json['id'],
        hashlib.sha256(str(json['mail']).encode()).hexdigest())
    response = {'message': f'La transaccion sera añadida al Bloque {index}'}
    return jsonify(response), 201

#descentralizando el blockchain

#conectar nuevos nodos
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node",401
    for node in nodes:
        blockchain.add_node(node)
    response = {'message':'Todos los nodos estan conectados, el blockchain contiene los siguientes nodos:','total_nodes':list(blockchain.nodes)}
    return jsonify(response),201

#reemmplazar la cadena por la mas larga
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replace = blockchain.replace_chain()
    if is_chain_replace:
        response = {'message':'Los nodos tenian diferentes cadenas, por lo que fue reemplazada por la mas larga', 'new_chain':blockchain.chain}
    else:
        response = {'message': 'La cadena es la mas larga','actual_chain':blockchain.chain}
    return jsonify(response), 200


app.run(host='0.0.0.0', port='5000')