from aiohttp import web
from routes import setup_routes
# from agent_controller import initialise
from holder_controller import initialize, send_and_store_credential
# from holder_controller import 
import asyncio
import aiohttp_cors
from views import *

# issuer_loop = asyncio.get_event_loop()
loop = asyncio.get_event_loop()

# issuer_loop.run_until_complete(initialize())
loop.run_until_complete(initialize())

app = web.Application()
# setup_routes(app)
# app.router.add_route("POST",'/requestRecord', record_request)
app.router.add_route("POST",'/approveAndStore', send_and_store_credential)
# app.router.add_route("POST",'/getRecord', getRecords)

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