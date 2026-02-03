"""EnvVar schema - separated to avoid circular imports."""

from pydantic import BaseModel


class EnvVar(BaseModel):
    """Environment variable model."""

    name: str
    value: str
