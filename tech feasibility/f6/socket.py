from __future__ import absolute_import, print_function, division
import socket

class Listener(object):

    def __init__(self, addr=('', 6560), backlog=5):
        self.sock = socket.socket()
        self.sock.bind(addr)
        self.sock.listen(backlog)

    def accept(self):
        return self.sock.accept()
