import sys, os

def main_in_pkg(fname):
    sys.path.insert(0, os.path.join(os.path.dirname(fname), '../'))
