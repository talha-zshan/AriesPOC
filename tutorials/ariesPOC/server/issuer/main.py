from aiohttp import web
# from routes import setup_routes
# from agent_controller import initialise
from issuer_controller import initialize
# from holder_controller import 
import asyncio
import aiohttp_cors
from views import *

loop = asyncio.get_event_loop()
# holder_loop = asyncio.get_event_loop()

loop.run_until_complete(initialize())
# holder_loop.run_until_complete(initialise())

app = web.Application()

# Credential issuance
app.router.add_route("POST",'/credential', send_credential)
app.router.add_route("POST", '/credential/issue', issue_credential)

# Schema, Connection and Credential Definition ID
app.router.add_route("POST",'/schema', add_schema)
app.router.add_route("GET", '/schema/{schema_name}/{schema_version}', getSchemaAndCredIDs)
app.router.add_route("GET",'/connection', get_connection_id)

# Proof and Verification
app.router.add_route("GET", '/proof-request', send_proof_request)
app.router.add_route('GET', '/verify', verify_proof)

# DID API Calls
app.router.add_route("GET", '/get-did', get_public_did)
app.router.add_route("GET", '/all-dids', get_all_dids)
app.router.add_route("GET", '/did-endpoint/{did}', get_did_endpoint)


# Configure default CORS settings.
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
})

# Configure CORS on all routes.
for route in list(app.router.routes()):
    cors.add(route)

web.run_app(app, host='0.0.0.0', port=8000)