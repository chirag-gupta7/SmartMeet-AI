def test_security_headers_present_on_api_responses(client):
    """Verify HTTP security response headers are returned on API endpoints."""
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
    assert (
        res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    )
