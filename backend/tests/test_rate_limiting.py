"""
Rate limiting tests — IP-based only.
Uses in-memory storage (UPSTASH_REDIS_PROTOCOL_URL="") to avoid
needing real Redis in CI.
"""
import os
import pytest
from fastapi.testclient import TestClient

# Force in-memory storage before importing the app
os.environ["UPSTASH_REDIS_PROTOCOL_URL"] = ""
os.environ.setdefault("UPSTASH_REDIS_URL", "test-url")
os.environ.setdefault("UPSTASH_REDIS_TOKEN", "test-token")

from main import app

client = TestClient(app, raise_server_exceptions=False)


class TestAnalyzeRateLimit:
    """POST /api/analyze enforces 5 requests/minute per IP."""

    def test_requests_within_limit_succeed(self):
        """First 5 requests from a fresh IP should not be rate-limited."""
        for i in range(5):
            response = client.post(
                "/api/analyze",
                json={"input_type": "text", "text": "Rate limit test."},
                headers={"X-Forwarded-For": f"192.168.10.{i + 1}"}
            )
            assert response.status_code != 429, \
                f"Request {i + 1} was unexpectedly rate-limited"

    def test_sixth_request_is_rate_limited(self):
        """After 5 requests from the same IP, the 6th must return 429."""
        test_ip = "10.0.1.100"
        headers = {"X-Forwarded-For": test_ip}
        payload = {"input_type": "text", "text": "Rate limit test."}

        for _ in range(5):
            client.post("/api/analyze", json=payload, headers=headers)

        response = client.post("/api/analyze", json=payload, headers=headers)
        assert response.status_code == 429

    def test_different_ips_have_independent_limits(self):
        """Two different IPs must have independent rate limit buckets."""
        payload = {"input_type": "text", "text": "Test."}

        # Exhaust limit for IP A
        for _ in range(5):
            client.post("/api/analyze", json=payload,
                        headers={"X-Forwarded-For": "10.0.2.1"})

        # IP A should now be blocked
        r_a = client.post("/api/analyze", json=payload,
                          headers={"X-Forwarded-For": "10.0.2.1"})
        assert r_a.status_code == 429

        # IP B has a fresh bucket — should not be blocked
        r_b = client.post("/api/analyze", json=payload,
                          headers={"X-Forwarded-For": "10.0.2.2"})
        assert r_b.status_code != 429

    def test_rate_limited_response_has_retry_after_header(self):
        """429 responses must include a Retry-After header."""
        test_ip = "10.0.3.1"
        headers = {"X-Forwarded-For": test_ip}
        payload = {"input_type": "text", "text": "Test."}

        for _ in range(5):
            client.post("/api/analyze", json=payload, headers=headers)

        response = client.post("/api/analyze", json=payload, headers=headers)
        assert response.status_code == 429
        assert (
            "retry-after" in response.headers or
            "Retry-After" in response.headers
        ), "429 response is missing Retry-After header"


class TestHealthEndpointLenient:
    """Health endpoint has a generous limit — must not block normal usage."""

    def test_health_not_blocked_at_normal_rate(self):
        for _ in range(10):
            r = client.get("/health")
            assert r.status_code == 200


class TestSwaggerNotRateLimited:
    """/docs and /openapi.json must never return 429."""

    def test_docs_never_rate_limited(self):
        for _ in range(20):
            r = client.get("/docs")
            assert r.status_code != 429

    def test_openapi_json_never_rate_limited(self):
        for _ in range(20):
            r = client.get("/openapi.json")
            assert r.status_code != 429


class TestAdminEndpoint:
    """POST /api/trending/refresh requires X-Admin-Key when configured."""

    def test_refresh_blocked_without_admin_key(self, monkeypatch):
        """When ADMIN_API_KEY is set, missing header returns 403."""
        monkeypatch.setenv("ADMIN_API_KEY", "secret-key-abc123")
        response = client.post("/api/trending/refresh")
        assert response.status_code == 403

    def test_refresh_allowed_with_correct_admin_key(self, monkeypatch):
        """Correct X-Admin-Key header must be accepted."""
        monkeypatch.setenv("ADMIN_API_KEY", "secret-key-abc123")
        response = client.post(
            "/api/trending/refresh",
            headers={"X-Admin-Key": "secret-key-abc123"}
        )
        assert response.status_code != 403

    def test_refresh_open_without_env_var(self, monkeypatch):
        """When ADMIN_API_KEY is not set, endpoint is open (dev mode)."""
        monkeypatch.delenv("ADMIN_API_KEY", raising=False)
        response = client.post("/api/trending/refresh")
        assert response.status_code != 403
