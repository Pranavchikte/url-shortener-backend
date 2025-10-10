# tests/test_api.py

def test_create_short_url(client):
    """
    Test creating a new short URL.
    """
    response = client.post(
        "/api/shorten",
        json={"original_url": "https://www.example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "short_code" in data
    assert len(data["short_code"]) == 6
    # FIX: Expect the trailing slash added by Pydantic's HttpUrl type
    assert data["original_url"] == "https://www.example.com/"

def test_redirect_to_url(client):
    """
    Test the redirect functionality.
    """
    create_response = client.post(
        "/api/shorten",
        json={"original_url": "https://www.google.com"}
    )
    short_code = create_response.json()["short_code"]

    redirect_response = client.get(f"/{short_code}", follow_redirects=False)
    
    assert redirect_response.status_code == 307
    # FIX: Expect the trailing slash in the location header
    assert redirect_response.headers["location"] == "https://www.google.com/"

def test_get_url_stats(client):
    """
    Test the analytics endpoint.
    """
    create_response = client.post(
        "/api/shorten",
        json={"original_url": "https://www.test-stats.com"}
    )
    short_code = create_response.json()["short_code"]

    stats_response = client.get(f"/api/stats/{short_code}")
    assert stats_response.status_code == 200
    data = stats_response.json()
    assert data["short_code"] == short_code
    assert data["total_clicks"] == 0
    assert "recent_clicks" in data

def test_not_found_error(client):
    """
    Test that a non-existent short code returns a 404 error.
    """
    response = client.get("/invalid", follow_redirects=False)
    assert response.status_code == 404
    assert response.json() == {"detail": "URL not found"}

def test_invalid_url_format(client):
    """
    Test that submitting an invalid URL returns a 422 validation error.
    """
    response = client.post(
        "/api/shorten",
        json={"original_url": "this-is-not-a-url"}
    )
    assert response.status_code == 422