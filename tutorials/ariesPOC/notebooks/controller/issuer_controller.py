import time
import asyncio
from aries_basic_controller.aries_controller import AriesAgentController

WEBHOOK_HOST = '0.0.0.0'
WEBHOOK_PORT = 8022
WEBHOOK_BASE = ""
ADMIN_URL = "http://alice-agent:8021"

API_KEY = "alice_api_123456789"

agent_controller = AriesAgentController(admin_url=ADMIN_URL, api_key=API_KEY)
agent_controller.init_webhook_server(webhook_host=WEBHOOK_HOST, webhook_port=WEBHOOK_PORT, webhook_base=WEBHOOK_BASE)

loop = asyncio.get_event_loop()
loop.create_task(agent_controller.listen_webhooks())

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
    print("Handle Credentials")
    exchange_id = payload['credential_exchange_id']
    state = payload['state']
    role = payload['role']
    attributes = payload['credential_proposal_dict']['credential_proposal']['attributes']
    print(f"Credential exchange {exchange_id}, role: {role}, state: {state}")
    print(f"Offering: {attributes}")
    
cred_listener = {
    "topic": "issue_credential",
    "handler": cred_handler
}

async def initialize():
    await agent_controller.listen_webhooks()
    agent_controller.register_listeners([connection_listener], defaults=True)

    # Check if agents are connected
    response = await agent_controller.connections.get_connections()
    results = response['results']
    print("Results : ", results)
    if len(results) > 0:
        connection = response['results'][0]
        print("Connection :", connection)
        if connection['state'] == 'active':       
            connection_id = connection["connection_id"]
            print("Active Connection ID : ", connection_id)
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


async def add_attributes(payload):
    connection_id = get_connectionID()
    schema_id = payload['schema_id']
    cred_def_id = payload['cred_def_id']
    attributes = payload['attributes']

    record = await agent_controller.issuer.send_credential(connection_id, schema_id, cred_def_id, attributes, auto_remove=False, trace=True)
    record_id = record['credential_exchange_id']
    state = record['state']
    role = record['role']
