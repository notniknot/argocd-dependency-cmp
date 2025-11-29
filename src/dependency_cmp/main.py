import logging
import sys
from pathlib import Path

from yaml import CDumper as Dumper
from yaml import dump_all

from dependency_cmp.discovery import collect_manifests_recursive
from dependency_cmp.graph import process_dag

# Import the new settings model
from dependency_cmp.settings import PluginSettings

# Initialize Settings (Loading Env Vars immediately)
try:
    settings = PluginSettings()
except Exception as e:
    # If config fails, we must print to stderr and exit non-zero
    print(f"Configuration Error: {e}", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger("dependency_cmp")


def main():
    try:
        # Log active configuration for debugging
        if settings.exclude_patterns:
            logger.info(f"Excluding patterns: {settings.exclude_patterns}")
        if settings.include_patterns:
            logger.info(f"Including patterns: {settings.include_patterns}")
        if settings.recurse:
            logger.info("Recursive search: Enabled")

        cwd = Path.cwd()

        # 1. Collect
        manifests = collect_manifests_recursive(
            cwd,
            recurse=settings.recurse,
            include=settings.include_patterns,
            exclude=settings.exclude_patterns,
        )

        # 2. Process
        final_manifests = process_dag(manifests)

        # 3. Output
        print(dump_all(final_manifests, Dumper=Dumper))

    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
