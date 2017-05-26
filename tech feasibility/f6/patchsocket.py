from __future__ import absolute_import, print_function, division
import socket

def patch(f):
    setattr(socket._socketobject, f.__name__, f)

@patch
def getline(sock):
    line = ''
    while True:
        ch = sock.recv(1)
        line += ch
        if ch == '\n':
            return line

@patch
def get_http_header(sock):
    lines = []
    while True:
        line = sock.getline()
        lines.append(line)
        if line == '\r\n':
            return lines

@patch
def get_nbytes(sock, n):
    r = ''
    while n:
        s = sock.recv(n)
        r += s
        n -= len(s)
    return r
