# Feature flags

Platform instances enable different features. Inspect them via `sdk.flags`:

```python
snapshot = await sdk.flags.get()          # fetched once, then cached
if await sdk.flags.is_enabled("workspace-ssh"):
    ...

await sdk.flags.refresh()                 # re-fetch after platform changes
```

SDK features that depend on a platform flag raise `FeatureNotEnabledError`
(or `FeatureNotAvailableError` if the instance doesn't have the feature at
all) *before* sending any request when the flag is off:

```python
from codesphere import FeatureNotAvailableError, FeatureNotEnabledError

try:
    await workspace.landscape.deploy()
except FeatureNotEnabledError as e:
    print(f"Enable the feature first: {e}")
except FeatureNotAvailableError as e:
    print(f"This platform does not support the feature: {e}")
```

You can also assert a flag yourself:

```python
await sdk.flags.require("msd")  # raises unless enabled
```

Flags are cached per client connection; call `sdk.flags.refresh()` to pick
up platform changes without reconnecting. Legacy platforms without the
flags endpoint are treated as having no flags (the SDK caches an empty
snapshot instead of failing).
