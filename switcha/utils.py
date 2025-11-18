import logging
from typing import Callable


def resize(items: list[any], n: int, make_item: Callable[[], any]):
    """Resize `items` list to length `n` inplace.

    If `len(items) > n`, then drop tail items.
    If `len(items) < n`, padding with items created by `make_item`.

    Returns:
        Modified `items`
    """
    assert n >= 0, f'invalid length {n}'

    n_items = len(items)

    if n == n_items:
        return items

    if n < n_items:
        items[:] = items[:n]

    if n > n_items:
        items.extend([make_item() for _ in range(n - n_items)])

    return items


def sync(items, keys, *, create=lambda d: d, key=lambda d: d):
    """Sync `items` list using `keys` set."""
    old_keys = {key(d) for d in items}

    keys_to_remove = old_keys - keys
    keys_to_create = keys - old_keys

    ret = []

    for item in items:
        if key(item) not in keys_to_remove:
            ret.append(item)

    for k in keys_to_create:
        ret.append(create(k))

    items[:] = ret

    return ret
