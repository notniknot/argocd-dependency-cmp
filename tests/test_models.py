from dependency_cmp.models import ResourceKey


def test_resource_key_properties():
    rk = ResourceKey("apps/v1", "Deployment", "my-app")
    assert rk.id == "apps/v1:Deployment:my-app"


def test_match_short_format():
    """Test matching 'Kind:Name' format."""
    rk = ResourceKey("apps/v1", "Deployment", "backend")

    # Exact match on Kind and Name
    assert rk.matches("Deployment:backend") is True

    # Case insensitive Kind
    assert rk.matches("deployment:backend") is True

    # Mismatch Name
    assert rk.matches("Deployment:frontend") is False

    # Mismatch Kind
    assert rk.matches("Service:backend") is False


def test_match_long_format():
    """Test matching 'apiVersion:Kind:Name' format."""
    rk = ResourceKey("apps/v1", "Deployment", "backend")

    # Exact match
    assert rk.matches("apps/v1:Deployment:backend") is True

    # Case insensitive Kind
    assert rk.matches("apps/v1:deployment:backend") is True

    # Mismatch API Version
    assert rk.matches("apps/v2:Deployment:backend") is False
    assert rk.matches("v1:Deployment:backend") is False


def test_match_invalid_format():
    rk = ResourceKey("v1", "Service", "db")
    # Missing parts
    assert rk.matches("db") is False
    assert rk.matches("") is False
