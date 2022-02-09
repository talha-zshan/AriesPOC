from aiohttp import web
from routes import setup_routes
# from agent_controller import initialise
from holder_controller import initialize
# from holder_controller import 
import asyncio
import aiohttp_cors
from views import *

# issuer_loop = asyncio.get_event_loop()
loop = asyncio.get_event_loop()

# issuer_loop.run_until_complete(initialize())
loop.run_until_complete(initialize())

app = web.Application()

# Accept Attr offered by issuer
app.router.add_route("GET", '/accept-issue', approveAndGet)
app.router.add_route("GET",'/accept-credential', accept_cred_request)

# Send Proof to Issuer
app.router.add_route('GET', '/send-proposal', send_proof_proposal)
app.router.add_route("GET",'/send-proof', send_proof)

# Get all credentials
app.router.add_route("GET", '/credentials', getAllCredentials)

# Test Stuff
app.router.add_route('GET', '/get_record/{cred_ex_id}', getRecordById )
app.router.add_route('GET','/get-all-records', get_all_records)
app.router.add_route('GET', '/my-credential', mycredential)
app.router.add_route("GET",'/request/{cred_ex_id}', recRequest)
app.router.add_route("GET",'/check/{cred_ex_id}', checkState)

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