import logging

from pydantic import BaseModel

log = logging.getLogger(__name__)


def update_model_fields(target: BaseModel, source: BaseModel) -> None:
    if log.isEnabledFor(logging.DEBUG):
        # Field names only — values may contain secrets (e.g. env vars).
        fields = ", ".join(sorted(source.model_fields_set))
        log.debug(f"Updating {target.__class__.__name__} fields: {fields}")

    for field_name in source.model_fields_set:
        value = getattr(source, field_name)
        setattr(target, field_name, value)
