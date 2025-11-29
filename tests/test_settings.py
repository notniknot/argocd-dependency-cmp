from dependency_cmp.settings import PluginSettings, parse_argo_glob_list

# --- Unit Tests for the Helper Function ---


def test_parse_none():
    assert parse_argo_glob_list(None) == []


def test_parse_argo_braces():
    assert parse_argo_glob_list("{config.yaml,*.json}") == ["config.yaml", "*.json"]


# --- Integration Tests for Pydantic Settings ---


def test_settings_defaults(monkeypatch):
    """Ensure defaults are set when no env vars are present."""
    # Clear relevant env vars to ensure clean state
    monkeypatch.delenv("PARAM_DIRECTORY_RECURSE", raising=False)
    monkeypatch.delenv("CMP_RECURSE", raising=False)

    settings = PluginSettings()
    assert settings.recurse is False
    assert settings.exclude_patterns == []


def test_settings_recurse_priority(monkeypatch):
    """Test that PARAM_DIRECTORY_RECURSE takes precedence over CMP_RECURSE."""
    monkeypatch.setenv("PARAM_DIRECTORY_RECURSE", "true")
    monkeypatch.setenv("CMP_RECURSE", "false")

    settings = PluginSettings()
    assert settings.recurse is True


def test_settings_complex_glob_parsing(monkeypatch):
    """Test that the Pydantic validator correctly parses Argo-style strings."""
    monkeypatch.setenv("PARAM_DIRECTORY_EXCLUDE", "{foo.yaml, .git/*}")

    settings = PluginSettings()
    assert settings.exclude_patterns == ["foo.yaml", ".git/*"]
