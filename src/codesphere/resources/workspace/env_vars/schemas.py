from ....core.base import CamelModel


class EnvVar(CamelModel):
    """Environment variable model."""

    name: str
    value: str
