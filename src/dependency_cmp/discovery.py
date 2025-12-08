import logging
import subprocess
import sys
from pathlib import Path

import yaml
from yaml import CLoader as Loader

from dependency_cmp.models import KUSTOMIZE_FILES

logger = logging.getLogger("dependency_cmp")


def match_pattern(path: Path, patterns: list[str]) -> bool:
    """Checks if path matches any glob pattern in the list."""
    if not patterns:
        return False
    return any(path.match(p) for p in patterns)


def has_kustomization(path: Path) -> bool:
    """Checks if a directory contains a Kustomization file."""
    return any((path / f).exists() for f in KUSTOMIZE_FILES)


def run_kustomize(path: Path):
    """Runs kustomize build on a directory."""
    logger.info(f"Running Kustomize in: {path}")
    try:
        cmd = ["kustomize", "build", str(path), "--enable-alpha-plugins"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return list(yaml.load_all(result.stdout, Loader=Loader))
    except subprocess.CalledProcessError as e:
        logger.error(f"Kustomize failed in {path}:\n{e.stderr}")
        sys.exit(1)


def read_raw_files(path: Path, include: list[str], exclude: list[str]):
    """Reads files in a directory respecting include/exclude patterns."""
    objects = []
    # Sort for deterministic order
    files = sorted([p for p in path.iterdir() if p.is_file()])

    for p in files:
        if exclude and match_pattern(p, exclude):
            continue
        if include:
            if not match_pattern(p, include):
                continue
        else:
            # Default behavior: Only read yaml/yml if no explicit include is passed
            if p.suffix not in (".yaml", ".yml"):
                continue

        try:
            with p.open("r") as f:
                docs = list(yaml.load_all(f, Loader=Loader))
                objects.extend([d for d in docs if d is not None])
        except Exception as e:
            logger.error(f"Failed to read file {p}: {e}")
            sys.exit(1)
    return objects


def collect_manifests_recursive(path: Path, recurse: bool, include: list[str], exclude: list[str]):
    """
    Discovery logic with support for directory.exclude and directory.include.
    """
    # Check if the directory itself is excluded (e.g. .git)
    if exclude and match_pattern(path, exclude):
        logger.debug(f"Skipping excluded directory: {path}")
        return []

    # Check for Kustomization (takes precedence over raw file scanning for this specific dir)
    kustomization_file = next((path / f for f in KUSTOMIZE_FILES if (path / f).exists()), None)
    if kustomization_file:
        # Check if the kustomization file itself is allowed
        # Logic: It must NOT be excluded. If include list exists, it MUST be included.
        is_excluded = exclude and match_pattern(kustomization_file, exclude)
        is_included = not include or match_pattern(kustomization_file, include)
        if not is_excluded and is_included:
            return run_kustomize(path)
        else:
            logger.info(f"Kustomization found but filtered out in {path}")

    collected_objects = []

    # Read Raw Files in current dir
    collected_objects.extend(read_raw_files(path, include, exclude))

    # Recurse (if enabled)
    if recurse:
        subdirs = sorted([p for p in path.iterdir() if p.is_dir()])
        for subdir in subdirs:
            collected_objects.extend(collect_manifests_recursive(subdir, recurse, include, exclude))

    return collected_objects
