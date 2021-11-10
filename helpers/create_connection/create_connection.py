import os
import asyncio
import time

from aries_basic_controller.aries_controller import AriesAgentController

from dotenv import load_dotenv
load_dotenv()

ALICE_WEBHOOK_HOST = '0.0.0.0'
ALICE_WEBHOOK_PORT = 8022
ALICE_WEBHOOK_BASE = ""
ALICE_ADMIN_URL = "http://alice-agent:8021"
ALICE_API_KEY = "alice_api_123456789"

# ALICE_ADMIN_URL = os.getenv('ALICE_ADMIN_URL')
# ALICE_WEBHOOK_PORT = os.getenv('ALICE_WEBHOOK_PORT')
# ALICE_WEBHOOK_HOST = os.getenv('ALICE_WEBHOOK_HOST')
# ALICE_WEBHOOK_BASE = os.getenv('ALICE_WEBHOOK_BASE')
# ALICE_API_KEY = os.getenv('ALICE_API_KEY')

BOB_WEBHOOK_HOST = "0.0.0.0"
BOB_WEBHOOK_PORT = 8052
BOB_WEBHOOK_BASE = ""
BOB_ADMIN_URL = "http://bob-agent:8051"

# BOB_ADMIN_URL = os.getenv('BOB_ADMIN_URL')
# BOB_WEBHOOK_PORT = os.getenv('BOB_WEBHOOK_PORT')
# BOB_WEBHOOK_HOST = os.getenv('BOB_WEBHOOK_HOST')
# BOB_WEBHOOK_BASE = os.getenv('BOB_WEBHOOK_BASE')


async def start_agent():

    time.sleep(10)

    # Inviter
    bob_agent_controller = AriesAgentController(admin_url=BOB_ADMIN_URL)

    # Invitee
    alice_agent_controller = AriesAgentController(
                                                admin_url=ALICE_ADMIN_URL,
                                                api_key=ALICE_API_KEY)

    # alice_agent_controller.init_webhook_server(
    #                                         webhook_host=ALICE_WEBHOOK_HOST,
    #                                         webhook_port=ALICE_WEBHOOK_PORT,
    #                                         webhook_base=ALICE_WEBHOOK_BASE)

    # await alice_agent_controller.listen_webhooks()
    #
    # await bob_agent_controller.listen_webhooks()
    #
    #
    # bob_agent_controller.register_listeners([], defaults=True)
    # alice_agent_controller.register_listeners([], defaults=True)

    invite = await bob_agent_controller.connections.create_invitation()
    print("Invite from BOB", invite)

    bob_connection_id = invite["connection_id"]
    print("Bob's connection ID for Alice", bob_connection_id)

    response = await alice_agent_controller.connections.accept_connection(invite["invitation"])


    print("Alice's Connection ID for Bob", response["connection_id"])
    alice_id = response["connection_id"]
    print("Invite Accepted")
    print("Alice's state for Bob's connection :", response["state"])


    time.sleep(10)

    # connection = await bob_agent_controller.connections.get_connection(bob_connection_id)
    # while connection["state"] != "request":
    #     time.sleep(1)
    #     connection = await bob_agent_controller.connections.get_connection(bob_connection_id)

    connection = await bob_agent_controller.connections.get_connection(bob_connection_id)
    print("Bob's Connection State for Alice :", connection["state"])

    all_conns = await bob_agent_controller.connections.get_connections()
    print("All Conns : ", all_conns)


    connection = await bob_agent_controller.connections.accept_request(bob_connection_id)
    print("Request Accepted")
    print(connection)

    print("BOB AGENT CONNECTION")
    print(connection)

    while connection["state"] != "active":
        trust_ping = await bob_agent_controller.messaging.trust_ping(bob_connection_id, "hello")
        print("TUST PING TO ACTIVATE CONNECTION - BOB -> RESEARCH")
        print(trust_ping)
        time.sleep(5)
        connection = await bob_agent_controller.connections.get_connection(bob_connection_id)

    trust_ping = await alice_agent_controller.messaging.trust_ping(alice_id,"hello")
    print("TUST PING TO ACTIVATE CONNECTION - RESEARCH -> BOB")
    print(trust_ping)

    print("ALICE ID {} BOB ID {}".format(alice_id, bob_connection_id))

    connection = await bob_agent_controller.connections.get_connection(bob_connection_id)
    print("BOB AGENT CONNECTION")
    print(connection)

    connection = await alice_agent_controller.connections.get_connection(alice_id)
    print("RESEARCH AGENT CONNECTION")
    print(connection)

    print("SUCCESS")
    time.sleep(2)
    await bob_agent_controller.terminate()
    await alice_agent_controller.terminate()


if __name__ == "__main__":
    # time.sleep(60)
    try:
        asyncio.get_event_loop().run_until_complete(start_agent())
    except KeyboardInterrupt:
        os._exit(1)
