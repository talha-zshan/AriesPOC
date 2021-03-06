import time
import asyncio
import logging
from aries_basic_controller.aries_controller import AriesAgentController

logger = logging.getLogger("holder_controller")


WEBHOOK_HOST = "0.0.0.0"
WEBHOOK_PORT = 8052
WEBHOOK_BASE = ""
ADMIN_URL = "http://bob-agent:8051"

agent_controller = AriesAgentController(admin_url=ADMIN_URL)

agent_controller.init_webhook_server(webhook_host=WEBHOOK_HOST, webhook_port=WEBHOOK_PORT, webhook_base=WEBHOOK_BASE)

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
# agent_controller.register_listeners([cred_listener], defaults=True)


async def initialise():
    await agent_controller.listen_webhooks()
    agent_controller.register_listeners([cred_listener], defaults=True)

    is_alive = False
    while not is_alive:
        try:
            await agent_controller.server.get_status()
            is_alive = True
            logger.info("Agent Active")
        except:
            time.sleep(5)

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
        print(f"Credential exchange {cred_ex_id}, role: {role}, state: {state}")
        print(f"Being offered: {attributes}")

        # Request Credential from Issuer
        res = request_record(cred_ex_id)


async def request_record(cred_ex_id):
    record = await agent_controller.issuer.send_request_for_record("cred_ex_id")
    state = record['state']
    role = record['role']
    print(f"Credential exchange {cred_ex_id}, role: {role}, state: {state}")    

async def store_credential(cred_ex_id):
    # Check if credential record is in credential_received state
    record = await agent_controller.issuer.get_record_by_id(cred_ex_id)
    state = record['state']
    role = record['role']
    print(f"Credential exchange {cred_ex_id}, role: {role}, state: {state}")
    
    # Store credential
    response = await agent_controller.issuer.store_credential(cred_ex_id, "My OM Credential")
    state = response['state']
    role = response['role']
    print(f"Credential exchange {cred_ex_id}, role: {role}, state: {state}")