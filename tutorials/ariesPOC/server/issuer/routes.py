from views import get_connection_id, add_schema, get_credential

def setup_routes(app):
    # app.router.add_get('/connection/new', invite)
    # app.router.add_get('/connection/{conn_id}/active', check_active)
    # app.router.add_get('/getConnection', get_connection_id)
    # app.router.add_get('/newSchema', add_schema)
    # app.router.add_get('/addAttributes', attributes_to_add)
    # app.router.add_route("GET",'/connection/new', invite)
    # app.router.add_route("GET",'/connection/{conn_id}/active', check_active)
    app.router.add_route("GET",'/getConnection', get_connection_id)
    app.router.add_route("POST",'/newSchema', add_schema)
    app.router.add_route("POST",'/addAttributes', get_credential)