from pathlib import Path

from dependency_cmp.discovery import collect_manifests_recursive


# Helper to create dummy yaml files
def create_yaml(path: Path, filename: str, content="kind: ConfigMap"):
    p = path / filename
    p.write_text(content)
    return p


def test_recurse_false_ignores_subdirs(tmp_path):
    # Setup: root file and subdir file
    create_yaml(tmp_path, "root.yaml")
    (tmp_path / "subdir").mkdir()
    create_yaml(tmp_path / "subdir", "nested.yaml")

    # Act: recurse=False
    results = collect_manifests_recursive(tmp_path, recurse=False, include=[], exclude=[])

    # Assert: Only 1 file found (root)
    assert len(results) == 1


def test_recurse_true_finds_nested(tmp_path):
    # Setup
    create_yaml(tmp_path, "root.yaml")
    (tmp_path / "subdir").mkdir()
    create_yaml(tmp_path / "subdir", "nested.yaml")

    # Act: recurse=True
    results = collect_manifests_recursive(tmp_path, recurse=True, include=[], exclude=[])

    # Assert: 2 files found
    assert len(results) == 2


def test_exclude_pattern(tmp_path):
    create_yaml(tmp_path, "keep_me.yaml")
    create_yaml(tmp_path, "ignore_me.yaml")

    # Act: Exclude 'ignore_me.yaml'
    results = collect_manifests_recursive(
        tmp_path, recurse=False, include=[], exclude=["ignore_me.yaml"]
    )

    assert len(results) == 1
    # We can't easily check the content object content here without digging into yaml parsing,
    # but the count proves filtering worked.


def test_include_pattern(tmp_path):
    create_yaml(tmp_path, "foo.yaml")
    create_yaml(
        tmp_path, "bar.txt"
    )  # Should be ignored by default anyway, but strictly ignored here
    create_yaml(tmp_path, "baz.json")

    # Act: Include only *.yaml
    results = collect_manifests_recursive(tmp_path, recurse=False, include=["*.yaml"], exclude=[])
    assert len(results) == 1


def test_kustomize_precedence(tmp_path, mocker):
    """
    If kustomization.yaml exists, we should CALL run_kustomize
    and NOT read raw yaml files in that directory.
    """
    # Setup: Directory has kustomization AND a raw yaml file
    create_yaml(tmp_path, "kustomization.yaml", content="resources: [other.yaml]")
    create_yaml(tmp_path, "other.yaml")

    # Mock the run_kustomize function in the discovery module
    # We return a dummy list to prove the mock was called
    mock_run = mocker.patch(
        "dependency_cmp.discovery.run_kustomize", return_value=[{"kind": "MockedObj"}]
    )

    # Act
    results = collect_manifests_recursive(tmp_path, recurse=False, include=[], exclude=[])

    # Assert
    mock_run.assert_called_once_with(tmp_path)
    assert len(results) == 1
    assert results[0]["kind"] == "MockedObj"


def test_kustomize_is_skipped_if_excluded(tmp_path, mocker):
    """If kustomization.yaml exists but is in exclude list, treat dir as raw files."""
    create_yaml(tmp_path, "kustomization.yaml")
    create_yaml(tmp_path, "raw.yaml")

    mock_run = mocker.patch("dependency_cmp.discovery.run_kustomize")

    # Act: Exclude the kustomization file specifically
    results = collect_manifests_recursive(
        tmp_path, recurse=False, include=[], exclude=["kustomization.yaml"]
    )

    # Assert
    mock_run.assert_not_called()
    assert len(results) == 1  # Should find raw.yaml

def test_multiple_kustomizations_recursive(tmp_path, mocker):
    """
    Test finding multiple kustomization.yaml files in different subdirectories
    when recurse=True.
    """
    # Setup structure:
    # /app1/kustomization.yaml
    # /app2/kustomization.yaml
    (tmp_path / "app1").mkdir()
    (tmp_path / "app2").mkdir()
    
    create_yaml(tmp_path / "app1", "kustomization.yaml")
    create_yaml(tmp_path / "app2", "kustomization.yaml")

    # Mock run_kustomize to return identifiable objects based on the path
    def side_effect(path):
        # We return a dummy object that indicates which folder was processed
        return [{"kind": "ConfigMap", "metadata": {"name": f"from-{path.name}"}}]

    mock_run = mocker.patch("dependency_cmp.discovery.run_kustomize", side_effect=side_effect)

    # Act
    results = collect_manifests_recursive(
        tmp_path, recurse=True, include=[], exclude=[]
    )

    # Assert
    # 1. run_kustomize should have been called twice
    assert mock_run.call_count == 2
    
    # 2. Results should contain objects from both apps
    names = [doc["metadata"]["name"] for doc in results]
    assert "from-app1" in names
    assert "from-app2" in names
