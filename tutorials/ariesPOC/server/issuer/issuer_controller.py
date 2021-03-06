import time
import asyncio
from aries_basic_controller.aries_controller import AriesAgentController
from aries_basic_controller.controllers.schema import SchemaController
import logging

logger = logging.getLogger("issuer_controller")

WEBHOOK_HOST = '0.0.0.0'
WEBHOOK_PORT = 8022
WEBHOOK_BASE = ""
ADMIN_URL = "http://alice-agent:8021"

API_KEY = "alice_api_123456789"

agent_controller = AriesAgentController(admin_url=ADMIN_URL, api_key=API_KEY,
                                        webhook_host=WEBHOOK_HOST, webhook_port=WEBHOOK_PORT, webhook_base=WEBHOOK_BASE)

def connection_handler(payload):
    print("Connection Handler Called")
    connection_id = payload["connection_id"]
    state = payload["state"]
    print(f"Connection {connection_id} in State {state}")


connection_listener = {
    "handler": connection_handler,
    "topic": "connections"
}


def cred_handler(payload):
    connection_id = payload['connection_id']
    exchange_id = payload['credential_exchange_id']
    state = payload['state']
    role = payload['role']
    print("\n---------------------------------------------------\n")
    print("Handle Issue Credential Webhook")
    print(f"Connection ID : {connection_id}")
    print(f"Credential exchange ID : {exchange_id}")
    print("Agent Protocol Role : ", role)
    print("Protocol State : ", state)
    print("\n---------------------------------------------------\n")

    if state == "offer_sent":
        proposal = payload["credential_proposal_dict"]
        attributes = proposal['credential_proposal']['attributes']
        print(f"Offering credential with attributes  : {attributes}")
        # YOUR LOGIC HERE
    elif state == "request_received":
        print("Request for credential received")
        # YOUR LOGIC HERE
        # response = await agent_controller.issuer.send_offer_for_record(exchange_id)

    elif state == "credential_sent":
        print("Credential Sent")
        # YOUR LOGIC HERE

# def cred_handler(payload):
#     print("Handle Credentials")
#     exchange_id = payload['credential_exchange_id']
#     state = payload['state']
#     role = payload['role']
#     nonce = payload['credential_offer']['nonce']
#     attributes = payload['credential_proposal_dict']['credential_proposal']['attributes']
#     print(f"Credential exchange {exchange_id}, role: {role}, state: {state}, none: {nonce}")
#     print(f"Offering: {attributes}")

cred_listener = {
    "topic": "issue_credential",
    "handler": cred_handler
}


async def initialize():
    await agent_controller.listen_webhooks()
    agent_controller.register_listeners([connection_listener], defaults=True)

    is_alive = False
    while not is_alive:
        try:
            await agent_controller.server.get_status()
            is_alive = True
            logger.info("Agent Active")
        except:
            time.sleep(5)

    # Check if agents are connected
    response = await agent_controller.connections.get_connections()
    results = response['results']
    connection_id = ""
    print("Results : ", results)
    if len(results) > 0:
        connection = response['results'][0]
        print("Connection :", connection)
        if connection['state'] == 'active':
            connection_id = connection["connection_id"]
            print("Active Connection ID : ", connection_id)
            return connection_id
    else:
        print("You must create a connection")
        raise Exception('No Connection between Agents')


async def create_invitation():
    invite = await agent_controller.connections.create_invitation()
    connection_id = invite["connection_id"]
    invite_message = invite['invitation']
    print("Connection ID", connection_id)
    print("Invitation")
    print(invite_message)


async def get_connectionID():
    response = await agent_controller.connections.get_connections()
    results = response['results']
    print("Results : ", results)
    if len(results) > 0:
        connection = response['results'][0]
        print("Connection :", connection)
        if connection['state'] == 'active':
            connection_id = connection["connection_id"]
            print("Active Connection ID : ", connection_id)
            return connection_id
    else:
        print("You must create a connection")
        raise Exception('No Connection between Agents')


async def write_schema_credential_definition(payload):
    schema_name = payload['schema_name']
    schema_version = payload['schema_version']
    attributes = payload['attributes']

    response = await agent_controller.schema.write_schema(schema_name, attributes, schema_version)
    schema_id = response['schema_id']

    res = await agent_controller.definitions.write_cred_def(schema_id)
    cred_def_id = res['credential_definition_id']

    return {'schema_id': schema_id,
            'cred_def_id': cred_def_id}


async def sendCredential(payload):
    print("Sending Credential")
    connection_id = payload['connection_id']
    schema_id = payload['schema_id']
    cred_def_id = payload['cred_def_id']
    attributes = payload['attributes']

    record = await agent_controller.issuer.send_credential(connection_id, schema_id, cred_def_id, attributes, auto_remove=False, trace=True)
    record_id = record['credential_exchange_id']
    state = record['state']
    role = record['role']
    nonce = record['credential_offer']['nonce']

    print("Entire Record")
    print(record)

    return {
        "cred_ex_id": record_id,
        "state": state,
        "role": role,
        "nonce": nonce
    }

async def issue_credential(payload):
    comment = payload['comment']
    cred_ex_id = payload['cred_ex_id']
    attributes = payload['attributes']

    response = await agent_controller.issuer.issue_credential(cred_ex_id, comment, attributes)

    return response


async def getSchemaAndCredDefIDs(payload):
    schema_name = payload['schema_name']
    schema_version = payload['schema_version']

    schemas = await agent_controller.schema.get_created_schema(schema_name=schema_name, schema_version=schema_version)
    cred_defs = await agent_controller.definitions.search_created(schema_name=schema_name, schema_version=schema_version)

    result = {
        'schema_ids': schemas,
        'cred_def_ids': cred_defs
    }

    return result


async def get_public_did():
    response = await agent_controller.wallet.get_public_did()
    did = response['result']['did']
    return did


async def get_all_dids():
    response = await agent_controller.wallet.get_dids()
    return {'dids': response}


async def get_did_endpoint(did):
    response = await agent_controller.wallet.get_did_endpoint(did=did)
    return {'endpoint': response}


# Verification
async def build_request(issuer_did):

    revocation = False
    SELF_ATTESTED = False
    exchange_tracing = False

    # Enable this to ask for attributes to identify a user
    req_attrs = [
        {"name": "name", "restrictions": [{"issuer_did": issuer_did}]},
        {"name": "email", "restrictions": [{"issuer_did": issuer_did}]},
    ]

    if revocation:
        req_attrs.append(
            {
                "name": "position",
                "restrictions": [{"issuer_did": issuer_did}],
                "non_revoked": {"to": int(time.time() - 1)},
            },
        )

    if SELF_ATTESTED:
        # test self-attested claims
        req_attrs.append({"name": "country"},)

    # Set predicates for Zero Knowledge Proofs
    req_preds = [
        # test zero-knowledge proofs
        {
            "name": "email",
            "p_type": ">=",
            "p_value": 21,
            "restrictions": [{"issuer_did": issuer_did}],
        }
    ]

    indy_proof_request = {
        "name": "Proof of Ownership",
        "version": "1.0",
        "requested_attributes": {
            f"0_{req_attr['name']}_uuid":
            req_attr for req_attr in req_attrs
        },
        "requested_predicates": {
            f"0_{req_pred['name']}_GE_uuid":
            req_pred for req_pred in req_preds
        },
    }

    if revocation:
        indy_proof_request["non_revoked"] = {"to": int(time.time())}

    #proof_request = indy_proof_request
    exchange_tracing_id = exchange_tracing
    proof_request_web_request = {
        "connection_id": await get_connectionID(),
        "proof_request": indy_proof_request,
        "trace": exchange_tracing,
    }

    return proof_request_web_request


async def proof_request():
    issuer_did = await get_public_did()
    proof_request_web_request = await build_request(issuer_did)

    response = await agent_controller.proofs.send_request(proof_request_web_request)
    print(response)
    print("\n")

    presentation_exchange_id = response['presentation_exchange_id']
    print("\n")

    print(presentation_exchange_id)

    result = {
        'presentation_exchange_id': presentation_exchange_id
    }

    return result


async def verify_presentation(presentation_exchange_id):
    verify = await agent_controller.proofs.verify_presentation(presentation_exchange_id)
    print(verify)

    print(verify['state'])
    print(verify['state'] == 'verified')

    for (name, val) in verify['presentation']['requested_proof']['revealed_attrs'].items():
        # This is the actual data that you want. It's a little hidden
        print(name + " : " + val['raw'])

    for (name, val) in verify['presentation']['requested_proof']['self_attested_attrs'].items():
        print(name + " : " + val)

    return "OK"


async def verify_proof(conn_id, role, state, cred_def_id, schema_id):
    response = await agent_controller.proofs.get_records(connection_id=conn_id, role=role, state=state)
    print(response)
    print('\n')

    results = response['results']
    request = find_proof_request(results, cred_def_id, schema_id)

    pres_ex_id = request['presentation_exchange_id']

    verify = await agent_controller.proofs.verify_presentation(pres_ex_id)

    return "OK"

def find_proof_request( results ,cred_def_id, schema_id):
    for req in results:
        iden = req['presentation']['identifiers'][0]
        if(iden['cred_def_id'] == cred_def_id and iden['schema_id'] == schema_id):
            return req
    return 0

    # results = await agent_controller.issuer.get_records()
    # if len(results) == 0:
    #     print("You need to first send a credential from the issuer (Alice)")
    #     return 0
    # else:
    #     all_cred_reqs = results["results"]
    #     for credential in all_cred_reqs:
    #         if(credential['credential_definition_id'] == cred_def_id and credential['schema_id'] == schema_id and credential['issuer_did'] == issuer_did and credential['schema_issuer_did'] == schema_issuer_did and credential['schema_name'] == schema_name and credential['schema_version'] == schema_version):
    #             return credential