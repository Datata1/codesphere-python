from ..core.models import CamelModel


class EnvVar(CamelModel):
    """Environment variable model."""

    name: str
    value: str
