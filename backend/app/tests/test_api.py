import pytest

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "DevMind" in data["service"]

@pytest.mark.asyncio
async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "DevMind AI" in data["name"]

@pytest.mark.asyncio
async def test_workspace_crud(client):
    # Create workspace
    payload = {
        "name": "Integration Test Workspace",
        "description": "Workspace for automated tests"
    }
    resp = await client.post("/api/v1/workspaces/", json=payload)
    assert resp.status_code == 200
    ws = resp.json()
    assert ws["name"] == payload["name"]
    assert "slug" in ws
    ws_id = ws["id"]

    # List workspaces
    list_resp = await client.get("/api/v1/workspaces/")
    assert list_resp.status_code == 200
    all_ws = list_resp.json()
    assert any(w["id"] == ws_id for w in all_ws)

    # Get single workspace
    get_resp = await client.get(f"/api/v1/workspaces/{ws_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == ws_id

@pytest.mark.asyncio
async def test_import_git_invalid_url(client):
    # Try importing an SSRF localhost url
    ws_resp = await client.post("/api/v1/workspaces/", json={"name": "SSRF Test Workspace"})
    ws_id = ws_resp.json()["id"]

    bad_payload = {
        "workspace_id": ws_id,
        "name": "Malicious Repo",
        "git_url": "http://127.0.0.1:9000/evil.git"
    }
    resp = await client.post("/api/v1/repositories/import-git", json=bad_payload)
    assert resp.status_code == 400
    assert "blocked" in resp.json()["detail"].lower() or "prohibited" in resp.json()["detail"].lower()
