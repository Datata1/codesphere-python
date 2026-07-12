"""Deprecated alias for :mod:`codesphere.resources.workspace.env_vars`."""

import warnings

from .env_vars import EnvVar, WorkspaceEnvVarManager

warnings.warn(
    "'codesphere.resources.workspace.envVars' is deprecated; "
    "import from 'codesphere.resources.workspace.env_vars' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["EnvVar", "WorkspaceEnvVarManager"]
