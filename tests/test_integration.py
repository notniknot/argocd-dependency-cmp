import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from dotenv import dotenv_values

# Path to the test cases
TEST_DATA_DIR = Path(__file__).parent / "test-data"


def get_test_cases():
    """
    Scans tests/test-data for subdirectories.
    Returns a list of directory names (e.g., ['simple-recurse', 'flat-deployment']).
    """
    if not TEST_DATA_DIR.exists():
        return []
    return [d.name for d in TEST_DATA_DIR.iterdir() if d.is_dir()]


def load_yaml_docs(content: str):
    """Parses a YAML string into a list of dicts, filtering None."""
    return [d for d in yaml.safe_load_all(content) if d is not None]


def k8s_sort_key(doc):
    """
    Generates a sort key for K8s resources to ignore document order.
    Key: (apiVersion, Kind, Namespace, Name)
    """
    meta = doc.get("metadata", {})
    return (doc.get("apiVersion"), doc.get("kind"), meta.get("namespace"), meta.get("name"))


@pytest.mark.parametrize("case_name", get_test_cases())
def test_data_driven_case(case_name, tmp_path):
    source_dir = TEST_DATA_DIR / case_name
    expected_file = source_dir / "expected.output"

    # 1. Validation
    if not expected_file.exists():
        pytest.fail(f"Test case '{case_name}' is missing 'expected.output' file.")

    # 2. Setup: Copy test case to a temp dir to avoid polluting source or git diffs
    run_dir = tmp_path / case_name
    shutil.copytree(source_dir, run_dir)

    # 3. Environment Setup
    # Look for a special 'params.env' file to set environment variables (e.g., RECURSE=true)
    env = os.environ.copy()
    env_file = run_dir / "params.env"
    if env_file.exists():
        config = dotenv_values(str(env_file))
        env.update(config)

    # 4. Execution
    # Runs the actual 'dependency_cmp' executable installed in the venv
    try:
        result = subprocess.run(
            ["uv", "run", "dependency_cmp"],
            cwd=run_dir,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        pytest.fail(f"dependency_cmp failed with exit code {e.returncode}.\nStderr: {e.stderr}")

    # 5. Parsing
    actual_docs = load_yaml_docs(result.stdout)
    expected_docs = load_yaml_docs(expected_file.read_text())

    # 6. Sorting (Normalization)
    # We sort both lists by Kind/Name so that order of documents doesn't matter
    actual_sorted = sorted(actual_docs, key=k8s_sort_key)
    expected_sorted = sorted(expected_docs, key=k8s_sort_key)

    # 7. Comparison
    # Using specialized assertion allows pytest to print diffs intelligently
    assert actual_sorted == expected_sorted
