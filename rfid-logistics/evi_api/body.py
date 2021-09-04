# -*- coding: utf-8 -*-
"""
Copyright (c) 2021 beyond-blockchain.org.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import bbc1
import binascii
import datetime
import hashlib
import json
import os
import string
import sys
import time
import xml.etree.ElementTree as ET
from bbc1.core import bbc_app, bbclib, bbc_config
from bbc1.core.bbc_error import *
from bbc1.core.ethereum import bbc_ethereum
from bbc1.core.message_key_types import KeyType
from bbc1.core.subsystem_tool_lib import wait_check_result_msg_type
from bbc1.lib import id_lib, registry_lib
from bbc1.lib.app_support_lib import Database, TransactionLabel
from bbc1.lib.app_support_lib import get_timestamp_in_seconds
from brownie import *
from flask import Blueprint, request, abort, jsonify, g

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from reader_tool import dict2xml


NAME_OF_DB = 'evi_db'

evi_evidence_table_definition = [
    ["digest", "BLOB"],
    ["key", "BLOB"],
    ["proof", "TEXT"],
]

IDX_DIGEST = 0
IDX_KEY    = 1
IDX_PROOF  = 2

evi_user_table_definition = [
    ["user_id", "BLOB"],
    ["name", "TEXT"],
    ["public_key", "BLOB"],
    ["private_key", "BLOB"],
]

IDX_USER_ID = 0
IDX_NAME    = 1
IDX_PUBKEY  = 2
IDX_PRIVKEY = 3

# As a matter of convenience, we need two users: the registry and its user.
NAME_REGISTRY = 'registry'
NAME_USER     = 'user'


domain_id = bbclib.get_new_id("rfid_logistics_domain", include_timestamp=False)


class Evidence:

    def __init__(self, digest, key, proof):
        self.digest = digest
        self.key = key
        self.proof = proof


    @staticmethod
    def from_row(row):
        return Evidence(row[IDX_DIGEST], row[IDX_KEY], row[IDX_PROOF])


class User:

    def __init__(self, user_id, name, keypair):
        self.user_id = user_id
        self.name = name
        self.keypair = keypair


    @staticmethod
    def from_row(row):
        return User(
            row[IDX_USER_ID],
            row[IDX_NAME],
            bbclib.KeyPair(privkey=row[IDX_PRIVKEY], pubkey=row[IDX_PUBKEY])
        )


class Store:

    def __init__(self):
        self.db = Database()
        self.db.setup_db(domain_id, NAME_OF_DB)


    def close(self):
        try:
            self.db.close_db(domain_id, NAME_OF_DB)
        except KeyError:
            pass


    def read_evidence(self, digest):
        rows = self.db.exec_sql(
            domain_id,
            NAME_OF_DB,
            'select * from evidence_table where digest=?',
            digest
        )
        if len(rows) <= 0:
            return None
        return Evidence.from_row(rows[0])


    def read_user(self, name):
        rows = self.db.exec_sql(
            domain_id,
            NAME_OF_DB,
            'select * from user_table where name=?',
            name
        )
        if len(rows) <= 0:
            return None
        return User.from_row(rows[0])


    def setup(self):
        self.db.create_table_in_db(domain_id, NAME_OF_DB, 'user_table',
                evi_user_table_definition, primary_key=IDX_USER_ID,
                indices=[IDX_NAME])
        self.db.create_table_in_db(domain_id, NAME_OF_DB, 'evidence_table',
                evi_evidence_table_definition, primary_key=IDX_DIGEST,
                indices=[IDX_KEY])


    def update_evidence_proof(self, evidence):
        self.db.exec_sql(
            domain_id,
            NAME_OF_DB,
            'update evidence_table set proof=? where digest=?',
            evidence.proof,
            evidence.digest
        )


    def write_evidence(self, evidence):
        self.db.exec_sql(
            domain_id,
            NAME_OF_DB,
            'insert into evidence_table values (?, ?, ?)',
            evidence.digest,
            evidence.key,
            evidence.proof
        )


    def write_user(self, user):
        self.db.exec_sql(
            domain_id,
            NAME_OF_DB,
            'insert into user_table values (?, ?, ?, ?)',
            user.user_id,
            user.name,
            user.keypair.public_key,
            user.keypair.private_key
        )


def abort_by_bad_content_type(content_type):
    abort(400, description='Content-Type {0} is not expected'.format(
            content_type))


def abort_by_bad_json_format():
    abort(400, description='Bad JSON format')


def abort_by_evidence_not_found():
    abort(404, description='Evidence is not found')


def abort_by_merkle_root_not_found():
    abort(404, description='Merkle root not stored (yet)')


def abort_by_subsystem_not_supported():
    abort(400, description='non-supported subsystem')


def abort_by_missing_param(param):
    abort(400, description='{0} is missing'.format(param))


def get_document(request):
    if request.headers['Content-Type'] != 'application/json':
        abort_by_bad_content_type(request.headers['Content-Type'])

    try:
        root = dict2xml(request.get_json())

    except Exception as e:
        s = str(e).split(':')
        if s[1].endswith('understand.'):
            abort_by_bad_json_format()
        else:
            s0 = s[0].split()
            abort(int(s0[0]), description=s[1].strip())

    id = root.findtext('id', default='N/A')
    return registry_lib.Document(
        document_id=bbclib.get_new_id(id, include_timestamp=False),
        root=root
    )


def run_client():
    client = bbc_app.BBcAppClient(port=bbc_config.DEFAULT_CORE_PORT,
            multiq=False, loglevel='all')
    client.set_user_id(bbclib.get_new_id('bbc1_examples.rfid_logistics',
            include_timestamp=False))
    client.set_domain_id(domain_id)
    client.set_callback(bbc_app.Callback())
    ret = client.register_to_core()
    assert ret
    return client


evi_api = Blueprint('evi_api', __name__)


@evi_api.after_request
def after_request(response):
    g.store.close()

    if g.idPubkeyMap is not None:
        g.idPubkeyMap.close()
    if g.registry is not None:
        g.registry.close()
    if g.client is not None:
        g.client.unregister_from_core()

    return response


@evi_api.before_request
def before_request():
    g.store = Store()
    g.idPubkeyMap = None
    g.registry = None
    g.client = None


@evi_api.route('/')
def index():
    return jsonify({})


@evi_api.route('/proof', methods=['GET'])
def get_proof_for_document():
    sDigest = request.json.get('digest')
    if sDigest is None:
        abort_by_missing_param('digest')

    digest = bytes(binascii.a2b_hex(sDigest))
    evidence = g.store.read_evidence(digest)

    if evidence is None:
        abort_by_evidence_not_found()

    if len(evidence.proof) > 0:
        return jsonify(json.loads(evidence.proof))

    g.client = run_client()

    g.client.verify_in_ledger_subsystem(None, digest)
    dat = wait_check_result_msg_type(g.client.callback,
            bbclib.MsgType.RESPONSE_VERIFY_HASH_IN_SUBSYS)

    dic = dat[KeyType.merkle_tree]

    if dic[b'result'] == False:
        abort_by_merkle_root_not_found()

    spec = dic[b'spec']
    if spec[b'subsystem'] != b'ethereum':
        abort_by_subsystem_not_supported()

    subtree = dic[b'subtree']

    spec_s = {}
    subtree_s = []

    for k, v in spec.items():
        spec_s[k.decode()] = v.decode() if isinstance(v, bytes) else v

    for node in subtree:
        subtree_s.append({
            'position': node[b'position'].decode(),
            'digest': node[b'digest'].decode()
        })

    dic = {
        'proof': {
            'spec': spec_s,
            'subtree': subtree_s
        }
    }

    evidence.proof = json.dumps(dic)
    g.store.update_evidence_proof(evidence)

    return jsonify(dic)


@evi_api.route('/evidence', methods=['POST'])
def register_evidence():
    sDigest = request.json.get('digest')
    if sDigest is None:
        abort_by_missing_param('digest')

    sKey = request.json.get('key')
    if sKey is None:
        abort_by_missing_param('key')

    digest = bytes(binascii.a2b_hex(sDigest))
    key = bytes(binascii.a2b_hex(sKey))

    g.store.write_evidence(Evidence(digest, key, ''))

    g.client = run_client()

    g.client.register_in_ledger_subsystem(None, digest)
    dat = wait_check_result_msg_type(g.client.callback,
            bbclib.MsgType.RESPONSE_REGISTER_HASH_IN_SUBSYS)

    return jsonify({
        'success': 'true'
    })


@evi_api.route('/setup', methods=['POST'])
def setup():
    g.store.setup()

    tmpclient = bbc_app.BBcAppClient(port=bbc_config.DEFAULT_CORE_PORT,
            multiq=False, loglevel="all")
    tmpclient.domain_setup(domain_id)
    tmpclient.callback.synchronize()
    tmpclient.unregister_from_core()

    g.idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)

    user_id, keypairs = g.idPubkeyMap.create_user_id(num_pubkeys=1)
    g.store.write_user(User(user_id, NAME_REGISTRY, keypair=keypairs[0]))

    user_id, keypairs = g.idPubkeyMap.create_user_id(num_pubkeys=1)
    g.store.write_user(User(user_id, NAME_USER, keypair=keypairs[0]))

    return jsonify({'domain_id': binascii.b2a_hex(domain_id).decode()})


@evi_api.route('/verify', methods=['GET'])
def verify_certificate():
    document = get_document(request)

    proof = request.json.get('proof')

    if proof is None:
        abort_by_missing_param('proof')

    spec = proof['spec']
    subtree = proof['subtree']

    # private key can be None as it is unused for viewing blockchain.
    eth = bbc_ethereum.BBcEthereum(
        spec['network'],
        private_key=None,
        contract_address=spec['contract_address'],
        project_dir=bbc1.__path__[0] + '/core/ethereum'
    )

    digest = hashlib.sha256(document.file()).digest()

    block_no, root = eth.verify_and_get_root(digest, subtree)

    if block_no <= 0:
        abort_by_merkle_root_not_found()

    block = network.web3.eth.getBlock(block_no)

    return jsonify({
        'network': spec['network'],
        'contract_address': spec['contract_address'],
        'block': block_no,
        'root': binascii.b2a_hex(root).decode(),
        'time': block['timestamp']
    })


@evi_api.errorhandler(400)
@evi_api.errorhandler(404)
@evi_api.errorhandler(409)
def error_handler(e):
    return jsonify({'error': {
        'code': e.code,
        'name': e.name,
        'description': e.description,
    }}), e.code


@evi_api.errorhandler(ValueError)
@evi_api.errorhandler(KeyError)
def error_handler(e):
    return jsonify({'error': {
        'code': 400,
        'name': 'Bad Request',
        'description': str(e),
    }}), 400


# end of evi_api/body.py
