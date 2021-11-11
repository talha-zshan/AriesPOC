from aiohttp import web
from aiohttp.web_response import json_response
import async_timeout
# from issuer_controller import agent_controller
import issuer_controller
import requests
import datetime
import secrets


# async def invite(request):
#     # Create Invitation
#     # wait for the coroutine to finish
#     with async_timeout.timeout(5):
#         invite = await agent_controller.connections.create_invitation()
#         connection_id = invite["connection_id"]
#         invite_url = invite["invitation_url"]
#         json_response = {"invite_url" : invite_url, "connection_id": connection_id}
#         return web.json_response(json_response)


# async def check_active(request: web.Request):

#     connection_id = request.match_info["conn_id"]

#     with async_timeout.timeout(2):

#         connection = await agent_controller.connections.get_connection(connection_id)
#         state = connection["state"]

#         is_active = state == "active"

#         json_response = {"active": is_active}

#         return web.json_response(json_response)


async def get_connection_id(self):
    
    connID = await issuer_controller.get_connectionID()

    json_response = {"connection_id": connID}

    return web.json_response(json_response)


async def add_schema(request):
    # request = web.Request
    payload = await request.json()

    print("MY PAYLOAD: ", payload)

    data = {
        'schema_name' : payload['schema_name'],
        'schema_version' : payload['schema_version'],
        'attributes': payload['attributes']
    }

    response = await issuer_controller.write_schema_credential_definition(data)

    print('Schema Added: ', response)
    result = {'data': response}

    return web.json_response(result)


async def send_credential(request):

    payload = await request.json()
    # connection_id = await issuer_controller.get_connectionID()
    response = await issuer_controller.sendCredential(payload)

    print('Attributes: ', response)
    result = {'credential': response}

    return web.json_response(result)



async def getSchemaAndCredIDs(request: web.Request):
    schema_name = request.match_info['schema_name']
    schema_version = request.match_info['schema_version']

    payload = {
        'schema_name' : schema_name,
        'schema_version' : schema_version
    }

    result = await issuer_controller.getSchemaAndCredDefIDs(payload)

    return web.json_response({'schema': result})
