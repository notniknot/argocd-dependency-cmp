from typing import Annotated, Union

from pydantic import BeforeValidator, Field
from pydantic_settings import BaseSettings


def parse_argo_glob_list(v: str | list[str] | None) -> list[str]:
    """
    Parses Argo CD glob pattern strings into a python list.
    Handles:
      - None/Empty -> []
      - "{a,b}" -> ["a", "b"]
      - "a,b"   -> ["a", "b"]
    """
    if v is None:
        return []
    if isinstance(v, list):
        return v

    val = str(v).strip()
    if not val:
        return []

    # Remove Argo-style braces if present
    if val.startswith("{") and val.endswith("}"):
        val = val[1:-1]

    return [p.strip() for p in val.split(",") if p.strip()]


ArgoGlobList = Annotated[Union[str, list[str]], BeforeValidator(parse_argo_glob_list)]


class PluginSettings(BaseSettings):
    """
    Configuration loaded from Environment Variables.
    """

    # Prioritizes the Param from the Plugin UI (PARAM_DIRECTORY_RECURSE)
    recurse: bool = Field(default=False, validation_alias="PARAM_DIRECTORY_RECURSE")

    # Matches 'directory.exclude' from plugin parameters
    exclude_patterns: ArgoGlobList = Field(default=[], validation_alias="PARAM_DIRECTORY_EXCLUDE")

    # Matches 'directory.include' from plugin parameters
    include_patterns: ArgoGlobList = Field(default=[], validation_alias="PARAM_DIRECTORY_INCLUDE")
