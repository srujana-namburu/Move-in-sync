import sys
import os
import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BACKEND_PATH)


try:
    import backend.models as models
    sys.modules["models"] = models
except Exception:
    pass

try:
    import backend.database as database
    sys.modules["database"] = database
except Exception:
    pass

try:
    import backend.routes as routes
    sys.modules["routes"] = routes
except Exception:
    pass



try:
    from backend.main import app
except Exception:
    app = None


@pytest.fixture
def client():
    if app:
        return TestClient(app)
    return None
