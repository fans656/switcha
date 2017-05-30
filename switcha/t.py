# coding: utf8
from window import Windows

wnds = Windows()
wnd = wnds[2]
s = u'新标签页'
print s.encode('gb2312')
print repr(wnd.title)
