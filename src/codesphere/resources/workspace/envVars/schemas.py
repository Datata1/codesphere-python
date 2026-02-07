from pydantic import BaseModel


class EnvVar(BaseModel):
    """Environment variable model."""

    name: str
    value: str
