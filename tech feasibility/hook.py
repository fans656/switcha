'''
http://pyhook.sourceforge.net/doc_1.5.0/
http://pyhook.sourceforge.net/doc_1.5.0/pyhook.HookManager.KeyboardEvent-class.html
https://msdn.microsoft.com/en-us/library/windows/desktop/dd375731(v=vs.85).aspx
'''
from PySide.QtCore import *
from PySide.QtGui import *
import pyHook
import win32con

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        self.hm = pyHook.HookManager()
        self.hm.KeyAll = self.onevent
        self.hm.HookKeyboard()

    def onevent(self, ev):
        if ev.KeyID == win32con.VK_TAB:
            if ev.Alt:
                if ev.Message in (
                        win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN):
                    print 'alt-tab down'
                    return False
                elif ev.Message in (
                    win32con.WM_KEYUP, win32con.WM_SYSKEYUP):
                    print 'alt-tab up'
                    return False
        print '.'
        return True

app = QApplication([])
w = Widget()
w.show()
app.exec_()
