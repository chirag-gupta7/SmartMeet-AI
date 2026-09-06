def test_security_headers_present_on_healthcheck(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert (
        response.headers.get("Referrer-Policy")
        == "strict-origin-when-cross-origin"
    )


def test_security_headers_present_on_auth_endpoint(client):
    response = client.post("/api/auth/login", json={})
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert (
        response.headers.get("Referrer-Policy")
        == "strict-origin-when-cross-origin"
    )
