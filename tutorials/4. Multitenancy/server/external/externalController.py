import time
import asyncio
import pprint
import sys
from termcolor import colored,cprint
from aiohttp import ClientConnectorError, ClientResponseError
from asyncio import CancelledError
import requests
import json 

from aries_basic_controller.aries_controller import AriesAgentController
   
# Create a small utility to print json formatted outout more human-readable    
pp = pprint.PrettyPrinter(indent=4)

WEBHOOK_HOST = "0.0.0.0"
WEBHOOK_BASE = ""

WEBHOOK_PORT = 8052
ADMIN_URL = "http://external-agent:8051"
SCHEMA_ID = '7DfSpFJMUThna1uQoR1mtY:2:PyDentity Multi-Tenant Tutorial:0.0.1'

agent_controller = AriesAgentController(admin_url=ADMIN_URL, webhook_host=WEBHOOK_HOST, webhook_port=WEBHOOK_PORT, webhook_base=WEBHOOK_BASE)


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

def connections_handler(payload):
    global STATE
    connection_id = payload["connection_id"]
    print("Connection message", payload, connection_id)
    STATE = payload['state']
    if STATE == 'active':
#         print('Connection {0} changed state to active'.format(connection_id))
        print(colored("Connection {0} changed state to active".format(connection_id), "red", attrs=["bold"]))


connection_listener = {
    "handler": connections_handler,
    "topic": "connections"
}
# agent_controller.register_listeners([cred_listener, connection_listener], defaults=True)


async def initialize():
    await agent_controller.listen_webhooks()
    agent_controller.register_listeners([cred_listener, connection_listener], defaults=True)
    
    await generatePublicDID()



async def generatePublicDID():
    response = await agent_controller.wallet.create_did()

    try:
        did_object = response['result']
        print("New DID", did_object)
    except:
        print("Unexpected error:", sys.exc_info()[0])

    url = 'https://selfserve.sovrin.org/nym'

    payload = {"network":"stagingnet","did": did_object["did"],"verkey":did_object["verkey"],"paymentaddr":""}

    # Adding empty header as parameters are being sent in payload
    headers = {}

    try:
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        print(r.json())
        print(r.status_code)
    except:
        print("Unexpected error:", sys.exc_info()[0])

    # Fetch and Accept the TAA
    TAA = ''
    try:
        response = await agent_controller.ledger.get_taa()
        TAA = response['result']['taa_record']
        TAA['mechanism'] = "service_agreement"
        print(TAA)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

    try:
        response = await agent_controller.ledger.accept_taa(TAA)
        ## Will return {} if successful
        print(response)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

    try:
        response = await agent_controller.wallet.assign_public_did(did_object["did"])
        pp.pprint(response)
    except:
        print("Unexpected error:", sys.exc_info()[0])


async def write_cred_def():
    try:
        response = await agent_controller.definitions.write_cred_def(SCHEMA_ID)
        cred_def_id = response["credential_definition_id"]
        print(cred_def_id)
    except ClientConnectorError as err:
        print(err)
    except ClientResponseError as err:
        print(err)


async def create_invite():
    try:
        invite = await agent_controller.connections.create_invitation(auto_accept=False)
        connection_id = invite["connection_id"]
        print("Connection ID", connection_id)
        print("Invitation Message - Copy This \n\n")
        invite_message = invite['invitation']
        print(invite_message)
        print("\n\n")
    except ClientConnectorError as err:
        print(err)
        # raise
    except ClientResponseError as err:
        print(err)


async def send_credential(connection_id, cred_def_id, credential_attributes):
    try:
        record = await agent_controller.issuer.send_credential(connection_id, SCHEMA_ID, cred_def_id, credential_attributes, trace=False)
        record_id = record['credential_exchange_id']
        state = record['state']
        role = record['role']
        credential_ex_id = record['credential_exchange_id']
        credential_id = record['credential_definition_id']
        print("Credential exchange ID: " + credential_ex_id + "\n")
        print("Credential ID: " + credential_id + "\n")
        print()
        print(f"Credential exchange {record_id}, role: {role}, state: {state}")
    except CancelledError as err:
        print("Asyncio CancelledError")
    except:
        raise    


async def check_connection(connection_id):
    try:
        # print('Current state for ConnectionId {} is {}'.format(connection_id,STATE))
        print(colored("Current state for ConnectionId {} is {}".format(connection_id,STATE), "magenta", attrs=["bold"]))
        while STATE != 'active':
        #     print('ConnectionId {0} is not in active state yet'.format(connection_id))
            print(colored("ConnectionId {0} is not in active state yet".format(connection_id), "yellow", attrs=["bold"]))
            trust_ping = await agent_controller.messaging.trust_ping(connection_id,'hello!')
        #     print('Trust ping send to ConnectionId {0} to activate connection'.format(trust_ping))
            print(colored("Trust ping send to ConnectionId {0} to activate connection".format(trust_ping), "blue", attrs=["bold"]))
            time.sleep(5)

        # print('ConnectionId: {0} is now active. Continue with notebook'.format(connection_id))
        print(colored("ConnectionId: {0} is now active. Continue with notebook".format(connection_id), "green", attrs=["bold"]))
    except ClientResponseError as err:
        print(err)    