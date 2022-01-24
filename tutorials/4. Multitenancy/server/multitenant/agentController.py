import time
import asyncio
import pprint

from aries_basic_controller.aries_controller import AriesAgentController
from aries_basic_controller.aries_tenant_controller import AriesTenantController

# Create a small utility to print json formatted outout more human-readable    
pp = pprint.PrettyPrinter(indent=4)

WEBHOOK_HOST = "0.0.0.0"
WEBHOOK_BASE = ""

WEBHOOK_PORT = 8022
ADMIN_URL = "http://multitenant-agent:8021"

# Based on the aca-py agent you wish to control
agent_controller = AriesAgentController(admin_url=ADMIN_URL, api_key="password", webhook_host=WEBHOOK_HOST, webhook_port=WEBHOOK_PORT, webhook_base=WEBHOOK_BASE,is_multitenant=True)

await agent_controller.listen_webhooks()


async def create_subwallet():
    payload = {
    "image_url": "https://aries.ca/images/sample.png",
    "key_management_mode": "managed",
    "label": "Alice",
    "wallet_dispatch_type": "default",
    "wallet_key": "MySecretKey1234",
    "wallet_name": "AlicesWallet",
    "wallet_type": "indy",
    }

    response_alice = await agent_controller.multitenant.create_subwallet(payload)
    wallet_id_alice = response_alice['wallet_id']

    pp.pprint(response_alice)

    return wallet_id_alice


async def get_auth_token(wallet_id_alice):
    response_alice = await agent_controller.multitenant.get_subwallet_authtoken_by_id(wallet_id_alice)
    alice_jwt = response_alice["token"]

    return alice_jwt


def connection_handler(payload):
    print("Alices Connection Handler Called")
    connection_id = payload["connection_id"]
    state = payload["state"]
    print(f"Connection {connection_id} in State {state}")
    
connection_listener = {
    "handler": connection_handler,
    "topic": "connections"
}

def messages_handler(payload):
    print("Alices Recieved a Message")
    connection_id = payload["connection_id"]

    print("Handle message", payload, connection_id)
    
message_listener = {
    "handler": messages_handler,
    "topic": "basicmessages"
}

# Based on the aca-py agent you wish to control
wallet_id_alice = await create_subwallet()
alice_agent_controller = AriesTenantController(admin_url=ADMIN_URL, wallet_id=wallet_id_alice, tenant_jwt=alice_jwt)
alice_agent_controller.register_listeners([message_listener,connection_listener], defaults=True)