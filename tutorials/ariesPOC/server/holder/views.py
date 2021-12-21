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


# async def record_request(request):
#     payload = await request.json()
#     response = await holder_controller.request_record(payload['cred_ex_id'])

#     print('Record Requested: ', response)
#     return web.json_response({'data': response})


async def sendAndStoreCredential(request):
    payload = await request.json()
    response = await holder_controller.send_and_store_credential(payload['cred_ex_id'])

    print('Credential Stored: ', response)
    return web.json_response({'data': response})

async def approveAndGet(self):
    res = await holder_controller.get_holder_records()
    json = {'data': res}
    return web.json_response(json)

async def send_proof(self):
    result = await holder_controller.send_presentation()
    return web.json_response(result)

async def send_proof_by_id(request: web.Request):
    payload = request.match_info['pres_ex_id']
    res = await holder_controller.send_presentation_by_id(payload)
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