from PySide import QtGui, QtCore
import numpy as np
from scipy.interpolate import interp1d, spline, PchipInterpolator
import sys
import os, shutil
from time import gmtime, strftime
import matplotlib as mpl
mpl.use('Qt4Agg')
mpl.rcParams['backend.qt4']='PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg

from bisect import bisect_left

compressed = []


def getfilesize(size, precision=2):
    """
    Get human readable filesizes of file.
    :param size:
    :param precision:
    :return:
    """
    suffixes = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
    suffixIndex = 0
    if size < 1024:
        return "%.*f%s" % (precision, size, suffixes[suffixIndex])
    else:
        while size >= 1024 and suffixIndex < 4:
            suffixIndex += 1
            size /= 1024.0
        return "%.*f %s" % (precision, size, suffixes[suffixIndex])


def loadFile(fname):
    global compressed

    print "before: ", getfilesize(os.path.getsize(fname), 2)
    before = os.path.getsize(fname)

    with open(fname) as f:
        lines = f.read().splitlines() 
    datas = []
    for line in lines: 
        datas.append(line.split(': '))

    last = datas[0]

    newd = []
    newd.append(last)

    for i in range(len(datas)):
        d = datas[i]
        if i == len(datas)-1:
            last = d
            newd.append(d)
        elif (float(d[0]) - float(last[0]) > 0.02 ):
            if d[1] != last[1]:
                last = d
                newd.append(d)

    # write out
    with open(fname, 'w') as f:
        for d in newd:
            f.write("%.2f" % float(d[0]))
            f.write(': '+ d[1])
            f.write('\n')

    print "after: ", getfilesize(os.path.getsize(fname), 2)
    after = os.path.getsize(fname)
    compressed.append(1.0 * after / before)
      

def loadFolder(name):

    ids = []
    for filename in os.listdir(name): 
        try:
            i = int(filename)
            ids.append(i)
        except ValueError:
            pass

    print ids

    for i in ids:
        fname = name + '/' + str(i)
        loadFile(fname)


def mainFolder(name):
    dirs = []
    for filename in os.listdir(name):
        dname = name + '/'+ filename
        if os.path.isdir(dname) and filename[0] == 's':
            print dname
            loadFolder(dname)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "need folder"
        sys.exit(0)

    #mainFolder(sys.argv[1])
    loadFolder(sys.argv[1])

    print "compression"
    print compressed
    print sum(compressed)/len(compressed)

