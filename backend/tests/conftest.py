import pytest

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Ensure no real API keys are used during tests."""
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")
    monkeypatch.setenv("HF_API_TOKEN", "test-token")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "test-key")
    monkeypatch.setenv("SEARCH_API_KEY", "test-key")
    monkeypatch.setenv("UPSTASH_REDIS_URL", "test-url")
    monkeypatch.setenv("UPSTASH_REDIS_TOKEN", "test-token")

@pytest.fixture(autouse=True)
def mock_network_calls(monkeypatch):
    """Mock httpx.AsyncClient and supabase client to prevent real network calls."""
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self._json_data = json_data
            self.status_code = status_code

        def json(self):
            return self._json_data

        def raise_for_status(self):
            pass

    class MockAsyncClient:
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, *args):
            pass

        async def get(self, *args, **kwargs):
            return MockResponse({})

        async def post(self, *args, **kwargs):
            return MockResponse({})

    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    # Mock supabase client if used
    try:
        import backend.lib.supabase_client as sc
        class MockSupabase:
            def table(self, name):
                return self
            def select(self, *args):
                return self
            def insert(self, *args):
                return self
            def update(self, *args):
                return self
            def eq(self, *args):
                return self
            def execute(self):
                class MockSupabaseResponse:
                    data = []
                return MockSupabaseResponse()
                
        monkeypatch.setattr(sc, "get_client", lambda: MockSupabase())
    except ImportError:
        pass
