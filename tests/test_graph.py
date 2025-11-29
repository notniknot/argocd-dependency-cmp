import pytest

from dependency_cmp.graph import process_dag


def test_simple_dependency():
    manifests = [
        {"apiVersion": "v1", "kind": "Service", "metadata": {"name": "db"}},
        {
            "apiVersion": "v1",
            "kind": "Deployment",
            "metadata": {
                "name": "app",
                "annotations": {"argocd-dependency-cmp/depends-on": "Service:db"},
            },
        },
    ]

    processed = process_dag(manifests)

    # Convert to map for easy lookup
    res_map = {m["metadata"]["name"]: m for m in processed}

    # DB should be Wave 0 (default/calculated 0)
    assert res_map["db"]["metadata"]["annotations"]["argocd.argoproj.io/sync-wave"] == "0"
    # App should be Wave 1
    assert res_map["app"]["metadata"]["annotations"]["argocd.argoproj.io/sync-wave"] == "1"


def test_missing_dependency_logs_warning(caplog):
    manifests = [
        {
            "apiVersion": "v1",
            "kind": "Deployment",
            "metadata": {
                "name": "app",
                "annotations": {"argocd-dependency-cmp/depends-on": "Service:ghost"},
            },
        }
    ]

    # Should not crash, just log warning
    processed = process_dag(manifests)

    assert "depends on 'Service:ghost', but it was not found" in caplog.text
    # Defaults to 0 if dependency missing
    assert processed[0]["metadata"]["annotations"]["argocd.argoproj.io/sync-wave"] == "0"


def test_cycle_detection():
    manifests = [
        {
            "apiVersion": "v1",
            "kind": "A",
            "metadata": {"name": "a", "annotations": {"argocd-dependency-cmp/depends-on": "B:b"}},
        },
        {
            "apiVersion": "v1",
            "kind": "B",
            "metadata": {"name": "b", "annotations": {"argocd-dependency-cmp/depends-on": "A:a"}},
        },
    ]

    with pytest.raises(SystemExit):
        process_dag(manifests)
