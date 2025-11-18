import io
import textwrap
import contextlib

from switcha.slots import Slots


def test_default(mocker):
    get_items = mocker.Mock()
    get_items.return_value = ['a', 'b', 'c']

    slots = Slots(get_items)
    verify(slots, '''
        a b c _
        _ _ _ _
    ''')

    slots.swap(1, 6)
    verify(slots, '''
        a _ c _
        _ _ b _
    ''')

    get_items.return_value = ['d', 'b', 'e', 'c', 'f']
    slots.update()
    verify(slots, '''
        d e c f
        _ _ b _
    ''')


def verify(slots, exp):
    got = show_slots(slots).strip().replace(' \n', '\n')
    exp = textwrap.dedent(exp).strip()
    if got != exp:
        print('=' * 40, 'expect')
        print(exp)
        print('=' * 40, 'got')
        print(got)
        assert False


def show_slots(*args, **kwargs):
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        _show_slots(*args, **kwargs)
    return f.getvalue()


def _show_slots(slots):
    for i_row in range(slots.n_rows):
        for i_col in range(slots.n_cols):
            slot = slots[i_row * slots.n_cols + i_col]
            if slot.item:
                print(slot.item, end=' ')
            else:
                print('_', end=' ')
        print()
