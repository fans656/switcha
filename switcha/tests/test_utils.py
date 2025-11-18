import pytest

from switcha.utils import (
    resize,
    sync,
)


class Test_resize:

    def test_padding(self):
        assert resize([], 3, lambda: 0) == [0, 0, 0]
        assert resize([1, 2], 3, lambda: 0) == [1, 2, 0]
        assert resize([1, 2], 4, lambda: 0) == [1, 2, 0, 0]

    def test_slice(self):
        assert resize([1, 2, 3], 2, lambda: 0) == [1, 2]
        assert resize([1, 2, 3], 0, lambda: 0) == []

    def test_noop(self):
        assert resize([], 0, lambda: 0) == []
        assert resize([1, 2, 3], 3, lambda: 0) == [1, 2, 3]

        with pytest.raises(AssertionError):
            resize([], -1, lambda: 0)


class Test_sync:

    def test_default(self):
        assert sync([], {1,2,3}) == [1,2,3]
        assert sync([1,2], {2,3}) == [2,3]
