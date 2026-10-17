def test_app_imports():
    from app import create_app
    assert callable(create_app)
