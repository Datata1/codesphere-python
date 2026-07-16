"""Drift guard: the generated sync surface must mirror the async surface.

Compares every public class of paired async/sync modules: same classes,
same public methods, same parameter lists. If this fails after touching
src/codesphere/_async, run `make sync-gen`; if it still fails, the
unasyncd configuration lost a construct.
"""

import importlib
import inspect
import pkgutil

import pytest

import codesphere._async as async_pkg

PAIRED_MODULES = sorted(
    name
    for _, name, _ in pkgutil.walk_packages(async_pkg.__path__, "codesphere._async.")
    if not name.endswith("._compat")
)


def _sync_name(async_module_name: str) -> str:
    return async_module_name.replace("codesphere._async", "codesphere._sync")


def _public_classes(module):
    return {
        name: obj
        for name, obj in vars(module).items()
        if inspect.isclass(obj)
        and not name.startswith("_")
        and obj.__module__ == module.__name__
    }


def _public_callables(cls):
    result = {}
    for name, member in inspect.getmembers(cls):
        if name.startswith("_"):
            continue
        if inspect.isfunction(member) or inspect.iscoroutinefunction(member):
            result[name] = member
    return result


def _param_signature(func) -> list[tuple[str, str, object]]:
    return [
        (p.name, str(p.kind), p.default)
        for p in inspect.signature(func).parameters.values()
    ]


@pytest.mark.parametrize("async_module_name", PAIRED_MODULES)
def test_module_surface_matches(async_module_name):
    async_module = importlib.import_module(async_module_name)
    sync_module = importlib.import_module(_sync_name(async_module_name))

    async_classes = _public_classes(async_module)
    sync_classes = _public_classes(sync_module)

    assert set(async_classes) == set(sync_classes), (
        f"class set differs in {async_module_name}"
    )

    for cls_name, async_cls in async_classes.items():
        sync_cls = sync_classes[cls_name]
        async_methods = _public_callables(async_cls)
        sync_methods = _public_callables(sync_cls)

        assert set(async_methods) == set(sync_methods), (
            f"method set differs on {async_module_name}.{cls_name}"
        )

        for method_name, async_method in async_methods.items():
            assert _param_signature(async_method) == _param_signature(
                sync_methods[method_name]
            ), f"signature differs: {async_module_name}.{cls_name}.{method_name}"
