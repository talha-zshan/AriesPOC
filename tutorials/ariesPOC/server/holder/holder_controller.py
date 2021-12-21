from os import stat
import time
import asyncio

from aries_basic_controller.aries_controller import AriesAgentController

WEBHOOK_HOST = "0.0.0.0"
WEBHOOK_PORT = 8052
WEBHOOK_BASE = ""
ADMIN_URL = "http://bob-agent:8051"

agent_controller = AriesAgentController(
    admin_url=ADMIN_URL, webhook_host=WEBHOOK_HOST, webhook_port=WEBHOOK_PORT, webhook_base=WEBHOOK_BASE)

# agent_controller.init_webhook_server(webhook_host=WEBHOOK_HOST, webhook_port=WEBHOOK_PORT, webhook_base=WEBHOOK_BASE)

# loop = asyncio.get_event_loop()
# loop.create_task(agent_controller.listen_webhooks())


def cred_handler(payload):
    print("Handle Credentials")
    exchange_id = payload['credential_exchange_id']
    state = payload['state']
    role = payload['role']
    attributes = payload['credential_proposal_dict']['credential_proposal']['attributes']
    print(f"Credential exchange {exchange_id}, role: {role}, state: {state}")
    print(f"Attributes: {attributes}")

cred_listener = {
    "topic": "issue_credential",
    "handler": cred_handler
}


agent_controller.register_listeners([cred_listener], defaults=True)


async def initialize():
    await agent_controller.listen_webhooks()
    agent_controller.register_listeners([cred_listener], defaults=True)

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


async def get_holder_records():
    response = await agent_controller.issuer.get_records()
    results = response["results"]
    if len(results) == 0:
        print("You need to first send a credential from the issuer (Alice)")
    else:
        cred_record = results[0]
        cred_ex_id = cred_record['credential_exchange_id']
        state = cred_record['state']
        role = cred_record['role']
        attributes = results[0]['credential_proposal_dict']['credential_proposal']['attributes']
        print(
            f"Credential exchange {cred_ex_id}, role: {role}, state: {state}")
        print(f"Being offered: {attributes}")

        # Request Credential from Issuer
        # res = await send_and_store_credential(cred_ex_id)
        # ret = store_credential(cred_ex_id)
        return cred_ex_id


async def get_record(record_id):
    cred_record = await agent_controller.issuer.get_record_by_id(record_id)
    print(cred_record)

    cred_ex_id = cred_record['credential_exchange_id']
    state = cred_record['state']
    role = cred_record['role']
    attributes = cred_record['credential_proposal_dict']['credential_proposal']['attributes']
    print(f"Credential exchange {cred_ex_id}, role: {role}, state: {state}")
    print(f"Being offered: {attributes}")

    return cred_ex_id

# async def send_credential(payload):
#     connection_id = payload['connection_id'] 
#     schema_id = payload['schema_id']
#     cred_def_id = payload['cred_def_id'] 
#     attributes = payload['attributes']

async def request_record(cred_ex_id):
    record = await agent_controller.issuer.send_request_for_record("cred_ex_id")
    state = record['state']
    role = record['role']
    print(f"Credential exchange {cred_ex_id}, role: {role}, state: {state}")

    return record


async def send_and_store_credential(cred_ex_id):

    c_ex_id = await get_record(cred_ex_id)
    record = await agent_controller.issuer.send_request_for_record(c_ex_id)
    state = record['state']
    role = record['role']
    print(f"Credential exchange {cred_ex_id}, role: {role}, state: {state}")

    # Check if credential record is in credential_received state
    record = await agent_controller.issuer.get_record_by_id(cred_ex_id)
    state = record['state']
    role = record['role']
    print(f"Credential exchange {cred_ex_id}, role: {role}, state: {state}")

    # Store credential
    response = await agent_controller.issuer.store_credential(cred_ex_id, "My Loyalty Credential")
    state = response['state']
    role = response['role']
    print(f"Credential exchange {cred_ex_id}, role: {role}, state: {state}")

    return response


async def send_presentation():
    response = await agent_controller.proofs.get_records()
    print(response)

    print('\n')

    state = response['results'][0]["state"]
    presentation_exchange_id = response['results'][0]['presentation_exchange_id']
    presentation_request = response['results'][0]['presentation_request']

    if state == "request_received":
        print("Received Request -> Query for credentials in the wallet that satisfy the proof request")
    
    # include self-attested attributes (not included in credentials)
    credentials_by_reft = {}
    revealed = {}
    self_attested = {}
    predicates = {}

    # select credentials to provide for the proof
    credentials = await agent_controller.proofs.get_presentation_credentials(presentation_exchange_id)
    print(credentials)

    if credentials:
        for row in sorted(
            credentials,
            key=lambda c: dict(c["cred_info"]["attrs"]),
            reverse=True,
        ):
            for referent in row["presentation_referents"]:
                if referent not in credentials_by_reft:
                    credentials_by_reft[referent] = row

    for referent in presentation_request["requested_attributes"]:
        if referent in credentials_by_reft:
            revealed[referent] = {
                "cred_id": credentials_by_reft[referent]["cred_info"][
                    "referent"
                ],
                "revealed": True,
            }
        else:
            self_attested[referent] = "South Africa"

    for referent in presentation_request["requested_predicates"]:
        if referent in credentials_by_reft:
            predicates[referent] = {
                "cred_id": credentials_by_reft[referent]["cred_info"][
                    "referent"
                ]
            }

    print("\nGenerate the proof")
    proof = {
        "requested_predicates": predicates,
        "requested_attributes": revealed,
        "self_attested_attributes": self_attested,
    }

    response = await agent_controller.proofs.send_presentation(presentation_exchange_id, proof)

    return response



async def send_presentation_by_id(pres_ex_id):
    response = await agent_controller.proofs.get_record_by_id(pres_ex_id)
    print(response)

    print('\n')

    state = response["state"]
    presentation_exchange_id = response['presentation_exchange_id']
    presentation_request = response['presentation_request']

    if state == "request_received":
        print("Received Request -> Query for credentials in the wallet that satisfy the proof request")
    
    # include self-attested attributes (not included in credentials)
    credentials_by_reft = {}
    revealed = {}
    self_attested = {}
    predicates = {}

    # select credentials to provide for the proof
    credentials = await agent_controller.proofs.get_presentation_credentials(presentation_exchange_id)
    print(credentials)

    if credentials:
        for row in sorted(
            credentials,
            key=lambda c: dict(c["cred_info"]["attrs"]),
            reverse=True,
        ):
            for referent in row["presentation_referents"]:
                if referent not in credentials_by_reft:
                    credentials_by_reft[referent] = row

    for referent in presentation_request["requested_attributes"]:
        if referent in credentials_by_reft:
            revealed[referent] = {
                "cred_id": credentials_by_reft[referent]["cred_info"][
                    "referent"
                ],
                "revealed": True,
            }
        else:
            self_attested[referent] = "South Africa"

    for referent in presentation_request["requested_predicates"]:
        if referent in credentials_by_reft:
            predicates[referent] = {
                "cred_id": credentials_by_reft[referent]["cred_info"][
                    "referent"
                ]
            }

    print("\nGenerate the proof")
    proof = {
        "requested_predicates": predicates,
        "requested_attributes": revealed,
        "self_attested_attributes": self_attested,
    }

    response = await agent_controller.proofs.send_presentation(presentation_exchange_id, proof)

    return response



# Test API Calls
async def send_req_for_rec(cred_ex_id):
    record = await agent_controller.issuer.send_request_for_record(cred_ex_id)
    state = record['state']
    role = record['role']
    print(f"Credential exchange {cred_ex_id}, role: {role}, state: {state}")
    return state


async def check_cred_state(cred_ex_id):
    record = await agent_controller.issuer.get_record_by_id(cred_ex_id)
    state = record['state']
    role = record['role']
    print(f"Credential exchange {cred_ex_id}, role: {role}, state: {state}")
    return state
