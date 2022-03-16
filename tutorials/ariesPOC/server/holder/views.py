from aiohttp import web
from aiohttp.web_response import Response
import async_timeout
from holder_controller import agent_controller
import holder_controller
import requests
import datetime
import secrets


async def invite(request):
    # Create Invitation
    # wait for the coroutine to finish
    with async_timeout.timeout(5):
        invite = await agent_controller.connections.create_invitation()
        connection_id = invite["connection_id"]
        invite_url = invite["invitation_url"]
        json_response = {"invite_url" : invite_url, "connection_id": connection_id}
        return web.json_response(json_response)


async def check_active(request: web.Request):

    connection_id = request.match_info["conn_id"]

    with async_timeout.timeout(2):

        connection = await agent_controller.connections.get_connection(connection_id)
        state = connection["state"]

        is_active = state == "active"

        json_response = {"active": is_active}

        return web.json_response(json_response)


async def accept_cred_request(request: web.Request):
    payload = await request.json()
    # parse the attributes
    cred_def_id = payload['cred_def_id']
    schema_id = payload['schema_id']

    res = await holder_controller.accept_credential(cred_def_id, schema_id)
    
    return web.json_response(res)




# Proof API Calls

async def send_proof_proposal():
    return 0

async def send_proof(request: web.Request):
    payload = await request.json()
    conn_id = payload['connection_id']
    result = await holder_controller.send_presentation(conn_id)
    return web.json_response(result)

async def send_proof_by_id(request: web.Request):
    payload = request.match_info['pres_ex_id']
    res = await holder_controller.send_presentation_by_id(payload)
    return web.json_response(res)


# Credential API Calls
async def getAllCredentials(self):
    res = await holder_controller.getAllCredentials()
    return web.json_response(res)

async def mycredential(request: web.Request):
    payload = await request.json()
    
    # parse the attributes
    cred_def_id = payload['cred_def_id']
    issuer_did = payload['issuer_did']
    schema_id = payload['schema_id']
    schema_issuer_did = payload['schema_issuer_did']
    schema_name = payload['schema_name']
    schema_version = payload['schema_version']

    res = holder_controller.find_credential(cred_def_id,issuer_did, schema_id, schema_issuer_did, schema_name, schema_version)
    
    return web.json_response(res)

# Test API Calls
async def recRequest(request: web.Request):
    cred_ex_id = request.match_info["cred_ex_id"]
    res = await holder_controller.send_req_for_rec(cred_ex_id)
    return web.json_response(res)

async def checkState(request: web.Request):
    cred_ex_id = request.match_info['cred_ex_id']
    res = await holder_controller.check_cred_state(cred_ex_id)
    return web.json_response(res)


async def getRecordById(request: web.Request):
    cred_ex_id = request.match_info['cred_ex_id']
    res = await holder_controller.get_record(cred_ex_id)
    return web.json_response(res)

async def get_all_records(self):
    res = await holder_controller.getAllRecords()
    return web.json_response(res)

