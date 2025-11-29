# Constants moved from utils.py
DEPENDS_ON_ANNOTATION = "argocd-dependency-cmp/depends-on"
SYNC_WAVE_ANNOTATION = "argocd.argoproj.io/sync-wave"
KUSTOMIZE_FILES = {"kustomization.yaml", "kustomization.yml", "Kustomization"}


class ResourceKey:
    """Helper to manage unique resource identifiers and matching logic."""

    def __init__(self, api_version, kind, name):
        self.api_version = api_version
        self.kind = kind
        self.name = name

    @property
    def id(self):
        """Unique ID for the graph: apiVersion:Kind:Name"""
        return f"{self.api_version}:{self.kind}:{self.name}"

    def matches(self, dep_str):
        """
        Checks if this resource matches a dependency string.
        Supported formats:
        1. "Kind:Name" (Partial match)
        2. "apiVersion:Kind:Name" (Exact match)
        """
        parts = dep_str.split(":")

        if len(parts) == 2:
            # Format: Kind:Name
            req_kind, req_name = parts
            return self.kind.lower() == req_kind.lower() and self.name == req_name

        elif len(parts) >= 3:
            # Format: apiVersion:Kind:Name
            # We assume the LAST two parts are Kind and Name. Everything before is apiVersion.
            req_name = parts[-1]
            req_kind = parts[-2]
            req_api = ":".join(parts[:-2])

            return (
                self.kind.lower() == req_kind.lower()
                and self.name == req_name
                and self.api_version == req_api
            )

        return False


def get_resource_key(doc):
    """Extracts metadata from a dict and returns a ResourceKey object."""
    kind = doc.get("kind", "Unknown")
    api_version = doc.get("apiVersion", "v1")
    metadata = doc.get("metadata") or {}
    name = metadata.get("name", "unnamed")
    return ResourceKey(api_version, kind, name)
