import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from dotenv import dotenv_values

TEST_DATA_DIR = Path(__file__).parent / "test-data"

# Config from Env
# Modes: "local", "docker-run" (spins new container), "docker-exec" (uses existing)
EXEC_MODE = os.environ.get("TEST_EXEC_MODE", "local")
DOCKER_IMAGE = os.environ.get("TEST_DOCKER_IMAGE", "argocd-dependency-cmp:dev")
CONTAINER_NAME = os.environ.get("TEST_CONTAINER_NAME", "integration-runner")


def get_test_cases():
    if not TEST_DATA_DIR.exists():
        return []
    return [d.name for d in TEST_DATA_DIR.iterdir() if d.is_dir()]


def load_yaml_docs(content: str):
    return [d for d in yaml.safe_load_all(content) if d is not None]


def k8s_sort_key(doc):
    meta = doc.get("metadata", {})
    return (doc.get("apiVersion"), doc.get("kind"), meta.get("namespace"), meta.get("name"))


@pytest.mark.parametrize("case_name", get_test_cases())
def test_data_driven_case(case_name, tmp_path):
    source_dir = TEST_DATA_DIR / case_name
    expected_file = source_dir / "expected.output"

    if not expected_file.exists():
        pytest.fail(f"Test case '{case_name}' is missing 'expected.output'.")

    run_dir = tmp_path / case_name
    shutil.copytree(source_dir, run_dir)

    env_vars = {}
    env_file = run_dir / "params.env"
    if env_file.exists():
        env_vars = dotenv_values(str(env_file))

    if EXEC_MODE == "docker-exec":
        cmd = ["docker", "exec", "-i"]  # -i for stdin/stdout
        for key, val in env_vars.items():
            cmd.extend(["-e", f"{key}={val}"])
        cmd.extend(["-w", f"/tests/test-data/{case_name}"])
        cmd.append(CONTAINER_NAME)
        cmd.append("dependency_cmp")
    elif EXEC_MODE == "local":
        cmd = ["uv", "run", "dependency_cmp"]
        os.environ.update(env_vars)
    else:
        pytest.fail(f"Unknown mode {EXEC_MODE}")

    try:
        kwargs = {"capture_output": True, "text": True, "check": True}
        if EXEC_MODE == "local":
            kwargs["cwd"] = run_dir
        result = subprocess.run(cmd, **kwargs)
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Execution failed.\nCommand: {cmd}\nStderr: {e.stderr}")

    actual_docs = load_yaml_docs(result.stdout)
    expected_docs = load_yaml_docs(expected_file.read_text())

    actual_sorted = sorted(actual_docs, key=k8s_sort_key)
    expected_sorted = sorted(expected_docs, key=k8s_sort_key)

    assert actual_sorted == expected_sorted
