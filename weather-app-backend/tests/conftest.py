
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """
    Fixture that provides a TestClient for the FastAPI app.
    This allows us to make mock HTTP requests to our API without running the server.
    """
    return TestClient(app)
