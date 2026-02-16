import pytest

def test_import_crud():
    try:
        import backend.crud
        assert True
    except Exception as e:
        pytest.fail(f"CRUD import failed: {e}")


def test_models_import():
    try:
        from backend.models import Base
        assert Base is not None
    except Exception as e:
        pytest.fail(f"Models import failed: {e}")
