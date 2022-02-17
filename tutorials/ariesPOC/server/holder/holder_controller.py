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


# def cred_handler(payload):
#     print("Handle Credentials")
#     exchange_id = payload['credential_exchange_id']
#     state = payload['state']
#     role = payload['role']
#     attributes = payload['credential_proposal_dict']['credential_proposal']['attributes']
#     print(f"Credential exchange {exchange_id}, role: {role}, state: {state}")
#     print(f"Attributes: {attributes}")

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
    print("Handle Credential Webhook Payload")

    if state == "offer_received":
        print("Credential Offer Recieved")
        proposal = payload["credential_proposal_dict"]
        print("The proposal dictionary is likely how you would understand and display a credential offer in your application")
        print("\n", proposal)
        print("\n This includes the set of attributes you are being offered")
        attributes = proposal['credential_proposal']['attributes']
        print(attributes)
        # YOUR LOGIC HERE
        # request = send_request_credential(exchange_id)

    elif state == "request_sent":
        print("\nA credential request object contains the commitment to the agents master secret using the nonce from the offer")
        # YOUR LOGIC HERE
    elif state == "credential_received":
        print("Received Credential")
        # YOUR LOGIC HERE
        response = agent_controller.issuer.store_credential(exchange_id,"New Credential")
    elif state == "credential_acked":
        # YOUR LOGIC HERE
        credential = payload["credential"]
        print("Credential Stored\n")
        print(credential)

        print("\nThe referent acts as the identifier for retrieving the raw credential from the wallet")
        # Note: You would probably save this in your application database
        credential_referent = credential["referent"]
        print("Referent", credential_referent)


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


# Credential Request and Acceptance Calls
async def accept_credential(cred_def_id, issuer_did, schema_id, schema_issuer_did, schema_name, schema_version):

    credential = await find_credential(cred_def_id=cred_def_id, issuer_did=issuer_did, schema_id=schema_id,
                                       schema_issuer_did=schema_issuer_did, schema_name=schema_name, schema_version=schema_version)

    state = credential['state']
    role = credential['role']
    attributes = credential['credential_proposal_dict']['credential_proposal']['attributes']
    cred_ex_id = credential['credential_exchange_id']

    res = await agent_controller.issuer.send_request_for_record(cred_def_id)

    print(
        f"Credential role: {role}, state: {state}")
    print(f"Being offered: {attributes}")


    return credential

# async def send_request_credential(cred_ex_id):
#     record = await agent_controller.issuer.send_request_for_record(cred_ex_id)
#     state = record['state']
#     role = record['role']
#     print(f"Credential exchange {cred_ex_id}, role: {role}, state: {state}")

#     return record

async def store_credential(cred_ex_id, name):
    res = await agent_controller.issuer.store_credential(cred_ex_id, name)
    return {"Cred_ex_id": cred_ex_id, "state": res['state']}


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



# Verification And Proof Calls
async def send_presentation(conn_id):
    response = await agent_controller.proofs.get_records(connection_id=conn_id)
    print(response)

    print('\n')

    results = response['results']
    state = results[0]["state"]
    presentation_exchange_id = results[0]['presentation_exchange_id']
    presentation_request = results[0]['presentation_request']

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
    # response = await agent_controller.proofs.get_records(connection_id=)
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



# Credential
async def getAllCredentials():
    record = await agent_controller.credentials.get_all()
    res = record['results']
    return res


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


async def getAllRecords():
    res = await agent_controller.issuer.get_records()
    results = res['results']
    return results


# Helper Functions
async def find_credential(cred_def_id, issuer_did, schema_id, schema_issuer_did, schema_name, schema_version):
    results = await agent_controller.issuer.get_records()
    if len(results) == 0:
        print("You need to first send a credential from the issuer (Alice)")
        return 0
    else:
        all_cred_reqs = results["results"]
        for credential in all_cred_reqs:
            # cred_proposal = credential['credential_proposal_dict']
            print(credential)
            if(credential['cred_def_id'] == cred_def_id and credential['schema_id'] == schema_id and credential['issuer_did'] == issuer_did and credential['schema_issuer_did'] == schema_issuer_did and credential['schema_name'] == schema_name and credential['schema_version'] == schema_version):
                return credential
