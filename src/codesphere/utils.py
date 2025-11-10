import logging
from pydantic import BaseModel
from typing import Any, Dict

log = logging.getLogger(__name__)


def update_model_fields(target: BaseModel, source: BaseModel) -> Dict[str, Any]:
    update_data = source.model_dump(exclude_unset=True)

    log.debug(f"Updating {target.__class__.__name__} with data: {update_data}")

    for key, value in update_data.items():
        setattr(target, key, value)

    return update_data
