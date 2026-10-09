"""The health check says which commit is running.

The deploy workflow polls /api/health until the body contains the SHA it just
deployed; that is how a green run proves the new version is live, not just
that some version answers.
"""

from app.config import settings

SHA = "0123456789abcdef0123456789abcdef01234567"


async def test_health_reports_the_running_commit(client, monkeypatch):
    monkeypatch.setattr(settings, "git_sha", SHA)

    resp = await client.get("/api/health")

    assert resp.status_code == 200
    assert resp.json()["git_sha"] == SHA


async def test_health_without_a_build_sha_says_unknown(client):
    resp = await client.get("/api/health")

    assert resp.status_code == 200
    assert resp.json()["git_sha"] == "unknown"
