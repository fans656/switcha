import itertools
import logging
from collections import defaultdict

import pyHook
import win32con
import win32api
from f6 import bunch

import config

__all__ = ['Keyboard']

logger = logging.getLogger(__name__)

class Keyboard(object):

    def __init__(self):
        self._seqs = []
        self._state = [k not in SYNTHESIS_KEYS and k in set(get_keys())
                       for k in xrange(255)]
        self._hook()

    def on(self, seq, callback):
        """Listen on specific key sequence

        Register callback on specific key stroke sequence.
        Sequence examples:
            'MENU TAB' - press `tab` while holding `alt`
            'MENU TAB^' - release `tab` while holding `alt`
            'CTRL ALT 1' - press `1` while holding ctrl and alt
            'LCTRL SPACE' - press `space(ASCII 0x20)` while holding `lctrl`
            'A B C' - press `c` while holding `a` and `b`
        The last key in sequence is the trigger, others are all modifiers.
        In order to match the sequence, you need to hold down all the
        modifiers, then press/release the trigger.
        See "Virtual-Key Codes (Windows)"[1] for the key names.
        Mapping rul is `<name> => VK_<name>`, for example:
            'MENU' - VK_MENU
            'LMENU' - VK_LMENU
            '1' - 0x31 which is ord('1')
            'A' - 0x41 which is ord('A'), NOTE that you can't use 'a'
                  (0x61 is for VK_NUMPAD1)
            'NUMBPAD1' - VK_NUMPAD1 (0x61)
        [1]: https://msdn.microsoft.com/en-us/library/windows/desktop/dd375731.aspx

        Args:
            seq - a str describing the key sequence
            callback - a callable with one argument (a `Sequence` object)
                to be called when the key sequence is detected

        Returns:
            [Sequence]
            E.g. 'alt f' => [(VK_LMENU, ord('f')), (VK_RMENU, ord('f'))]
        """
        if not callable(callback):
            callback = id
            logger.warning(
                'invalid callback in sequence "{}", will use nop'.format(seq))
        try:
            seqs = parse_seq(seq)
            for seq in seqs:
                seq.callback = callback
                self._seqs.append(seq)
                logger.info('register {} '.format(repr(seq)))
            return seqs
        except ValueError as e:
            logger.warning(e.message)

    def run(self):
        """Helpler method to begin an event loop"""
        from PySide.QtCore import QCoreApplication
        app = QCoreApplication([])
        app.exec_()

    def _onkey(self, ev):
        ev = KeyEvent(ev)
        logger.debug('{:>8}({}) {:4}'.format(
            ev.Key, hex(ev.KeyID), 'DOWN' if ev.down else 'UP'))
        self._state[ev.KeyID] = ev.down
        if not ev.down:
            assert ev.up
            #print map(int, self._state)
            #print signature_str(self.downs)
        sig = self.downs
        logger.debug('downs: {}'.format(signature_str(sig)))
        #print map(signature_str, self._seqs.keys())
        for seq in self._seqs:
            if sig != seq.signature:
                continue
            logger.debug('sig match | ev: {}({}), trigger: {}({})'.format(
                to_name(ev.KeyID), updown(up=ev.up),
                to_name(seq.trigger), updown(up=seq.up)
            ))
            match = ev.KeyID == seq.trigger and ev.up == seq.up
            if match:
                logger.info('"{}" detected'.format(str(seq)))
                r = seq.callback(seq)
                if r is None:
                    return 1
                return 1 if r else 0
        return 1

    @property
    def downs(self):
        return tuple(vk for vk, down in enumerate(self._state) if down)

    @property
    def ups(self):
        return tuple(vk for vk, down in enumerate(self._state) if not down)

    def _hook(self):
        self.hm = pyHook.HookManager()
        self.hm.KeyAll = self._onkey
        self.hm.HookKeyboard()

class Sequence(object):

    def __init__(self, trigger, up, modifiers, signature, seq, callback=None):
        self.trigger = trigger
        self.up = up
        self.modifiers = modifiers
        self.signature = signature
        self.seq = seq
        self.callback = callback

    def __str__(self):
        return self.seq

    def __repr__(self):
        to_sig = lambda sig: ','.join(map(to_name, sig))
        return ('Sequence(seq="{}", modifiers={}, trigger={}, '
                'sig=[{}], up={})'.format(
                    self.seq,
                    to_sig(self.modifiers),
                    to_name(self.trigger),
                    to_sig(self.signature),
                    self.up))

def parse_seq(seq):
    names = seq.split()
    if not names:
        raise ValueError('empty sequence')
    modifiers = names[:-1]
    trigger = names[-1]
    up = trigger.endswith('^')
    if up:
        names[-1] = trigger[:-1]
    keys = [to_key(name) for name in names]
    unrecognized_names = [name for name, key in zip(names, keys) if not key]
    if unrecognized_names:
        raise ValueError('unrecognized key names {} '
                         'in key sequence "{}"'.format(
                             unrecognized_names, seq))
    uniq_keys = set(keys)
    if len(keys) != len(uniq_keys):
        logger.warning('duplicate keys in sequence "{}"'.format(seq))
    keys_a = itertools.product(*(SYNTHESIS_KEYS.get(key, [key]) for key in keys))
    return [Sequence(trigger=keys[-1], up=up, modifiers=keys[:-1],
                     signature=tuple(sorted(keys[:-1] if up else keys)),
                     seq=seq)
            for keys in keys_a]

class KeyEvent(object):

    def __init__(self, ev):
        self.ev = ev
        self.down = self.Message in (
            win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN)
        self.up = not self.down

    def __getattr__(self, attr):
        return getattr(self.ev, attr)

ALIASES = {
    'CTRL': 'CONTROL',
    'LCTRL': 'LCONTROL',
    'RCTRL': 'RCONTROL',
    'ALT': 'MENU',
    'LALT': 'LMENU',
    'RALT': 'RMENU',
}
NAME2VK = {name[3:]: getattr(win32con, name) for name in dir(win32con)
           if name.startswith('VK_')}
VK2NAME = {vk: name for name, vk in NAME2VK.items()}
SYNTHESIS_KEYS = {
    win32con.VK_CONTROL: (
        win32con.VK_LCONTROL,
        win32con.VK_RCONTROL,
    ),
    win32con.VK_MENU: (
        win32con.VK_LMENU,
        win32con.VK_RMENU,
    ),
    win32con.VK_SHIFT: (
        win32con.VK_LSHIFT,
        win32con.VK_RSHIFT,
    ),
}

def get_keys():
    return tuple(k for k in xrange(255)
                 if win32api.GetAsyncKeyState(k) & 0x8000)

def to_name(key):
    return VK2NAME.get(key, None) or chr(key)

def to_key(name):
    name = name.upper()
    name = ALIASES.get(name, name)
    try:
        r = NAME2VK.get(name, None) or ord(name)
    except TypeError:
        return None
    return min(r, 255)

def signature_str(sig):
    return map(to_name, sig)

def updown(down=None, up=None):
    if up is None:
        up = not down
    elif down is None:
        down = not up
    return 'UP' if up else 'DOWN'

if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    #logger.setLevel(logging.INFO)
    kbd = Keyboard()
    seq = kbd.on('ctrl alt', id)
    seq = kbd.on('alt ctrl', id)
    kbd.run()
