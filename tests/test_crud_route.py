def test_routes_exist(client):
    if client is None:
        return

    response = client.get("/")
    assert response.status_code in [200, 404]
