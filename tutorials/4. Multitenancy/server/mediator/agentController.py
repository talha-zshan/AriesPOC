import time
import asyncio

from aries_basic_controller.aries_controller import AriesAgentController
    
WEBHOOK_HOST = "0.0.0.0"
WEBHOOK_PORT = 8042
WEBHOOK_BASE = ""
ADMIN_URL = "http://mediator-agent:8041"

# Based on the aca-py agent you wish to control
agent_controller = AriesAgentController(admin_url=ADMIN_URL, webhook_host=WEBHOOK_HOST, webhook_port=WEBHOOK_PORT, webhook_base=WEBHOOK_BASE)

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

agent_controller.register_listeners([connection_listener], defaults=True)

async def create_invite():
    # Create Invitation
    invite = await agent_controller.connections.create_invitation(multi_use="true")
    connection_id = invite["connection_id"]
    invite_message = invite['invitation']
    print("Connection ID", connection_id)
    print("Invitation")
    print(invite_message)

async def mediation_records():
    response = await agent_controller.mediation.get_mediation_records()

    for record in response:
        print("Mediation Record")
        print("connection_id", record["connection_id"])
        print("State", record["state"])
    await agent_controller.connections.accept_connection(record["connection_id"])