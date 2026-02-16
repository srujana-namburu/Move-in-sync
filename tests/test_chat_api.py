def test_chat_api_import():
    try:
        import backend.Agents
        assert True
    except Exception as e:
        assert False, f"Agent import failed: {e}"
