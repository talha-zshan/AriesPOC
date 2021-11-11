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
# setup_routes(app)
app.router.add_route("GET",'/getConnection', get_connection_id)
app.router.add_route("POST",'/newSchema', add_schema)
app.router.add_route("POST",'/sendCredential', send_credential)
app.router.add_route("GET", '/getSchemaAndCred/{schema_name}/{schema_version}', getSchemaAndCredIDs)

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