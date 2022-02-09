from aiohttp import web
from aiohttp.web_response import json_response
import async_timeout
# from issuer_controller import agent_controller
import issuer_controller
import requests
import datetime
import secrets


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
    # result = {'data': response}

    return web.json_response(response)


async def send_credential(request):

    payload = await request.json()
    # connection_id = await issuer_controller.get_connectionID()
    response = await issuer_controller.sendCredential(payload)

    print('Attributes: ', response)
    # result = {'credential': response}

    return web.json_response(response)

async def issue_credential(request):
    payload = await request.json()
    # cred_ex_id = payload['cred_ex_id']

    response = await issuer_controller.issue_credential(payload)

    return response

async def getSchemaAndCredIDs(request: web.Request):
    schema_name = request.match_info['schema_name']
    schema_version = request.match_info['schema_version']

    payload = {
        'schema_name' : schema_name,
        'schema_version' : schema_version
    }

    result = await issuer_controller.getSchemaAndCredDefIDs(payload)

    return web.json_response(result)

async def send_proof_request(self):
    result = await issuer_controller.proof_request()
    return web.json_response(result)


async def verify_presentation(request: web.Request):
    pres_ex_id = request.match_info['pres_ex_id']
    result = await issuer_controller.verify_presentation(pres_ex_id)

    return web.json_response(result)

async def get_public_did(self):
    result = await issuer_controller.get_public_did()
    return web.json_response(result)


# Testng DID Stuff

async def get_all_dids(self):
    result = await issuer_controller.get_all_dids()
    return web.json_response(result)

async def get_did_endpoint(request: web.Request):
    did = request.match_info['did']
    result = await issuer_controller.get_did_endpoint(did)
    return web.json_response(result)

async def resolve_did(request: web.Request):
    did = request.match_info['did']
    result = ''
    return web.json_response(result)