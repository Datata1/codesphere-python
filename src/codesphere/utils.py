import logging

from pydantic import BaseModel

log = logging.getLogger(__name__)


def update_model_fields(target: BaseModel, source: BaseModel) -> None:
    if log.isEnabledFor(logging.DEBUG):
        debug_dump = source.model_dump(exclude_unset=True)
        log.debug(f"Updating {target.__class__.__name__} with data: {debug_dump}")

    for field_name in source.model_fields_set:
        value = getattr(source, field_name)
        setattr(target, field_name, value)
