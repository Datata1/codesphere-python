import logging
from pydantic import BaseModel
from typing import Any, Dict, List, Type, TypeVar

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def update_model_fields(target: BaseModel, source: BaseModel) -> None:
    if log.isEnabledFor(logging.DEBUG):
        debug_dump = source.model_dump(exclude_unset=True)
        log.debug(f"Updating {target.__class__.__name__} with data: {debug_dump}")

    for field_name in source.model_fields_set:
        value = getattr(source, field_name)
        setattr(target, field_name, value)


def dict_to_model_list(
    data: Dict[Any, Any],
    model_cls: Type[T],
    key_field: str = None,
    value_field: str = None,
) -> List[T]:
    if key_field is None or value_field is None:
        for name, field_info in model_cls.model_fields.items():
            if field_info.json_schema_extra:
                if field_info.json_schema_extra.get("is_dict_key"):
                    key_field = name
                elif field_info.json_schema_extra.get("is_dict_value"):
                    value_field = name

    if not key_field or not value_field:
        raise ValueError(
            f"Could not determine key/value mapping for {model_cls.__name__}. "
            "Please explicitly pass key_field/value_field OR mark fields in the model."
        )

    items = []
    for key, value in data.items():
        item = model_cls(**{key_field: key, value_field: value})
        items.append(item)

    return items
