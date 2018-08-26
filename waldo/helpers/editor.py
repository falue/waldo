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


def takeClosest(myList, myNumber):
    """
    Assumes myList is sorted. Returns closest value to myNumber.

    If two numbers are equally close, return the smallest number.
    """
    pos = bisect_left(myList, myNumber)
    if pos == 0:
        return pos
    if pos == len(myList):
        return pos-1
    before = myList[pos - 1]
    after = myList[pos]
    if after - myNumber < myNumber - before:
        return pos
    else:
        return pos-1


def add(x,y):
    global dots
    print "adding", x, y
    dots.append([x, y])
    dots.sort()


def remove(x,y):
    global dots
    print "removing"
    xs = [float(item[0]) for item in dots]
    idx = takeClosest(xs, x)
    dots.pop(idx)


folderName = ''

dots = []
plotdots = []
mode = add


def interpol():
    global plotdots

    if len(dots) > 1:
        x = [float(item[0]) for item in dots]
        y = [int(item[1]) for item in dots]

        pchip = PchipInterpolator(x,y)

        newx = np.arange(min(x), max(x), 0.005)
        newy = pchip(newx)

        newdots = []
        for i in range(len(newx)):
            newdots.append([newx[i], newy[i]])

        plotdots = newdots

    else:
        plotdots = []


class MyWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)

        self.pushButtonPlot = QtGui.QPushButton(self)
        self.pushButtonPlot.setText("erase all")
        self.pushButtonPlot.clicked.connect(self.on_pushButtonPlot_clicked)

        self.removerButton = QtGui.QPushButton(self)
        self.removerButton.setText("remover")
        self.removerButton.clicked.connect(self.removerButton_clicked)

        self.adderButton= QtGui.QPushButton(self)
        self.adderButton.setText("adder")
        self.adderButton.clicked.connect(self.adderButton_clicked)

        self.zeroButton= QtGui.QPushButton(self)
        self.zeroButton.setText("first/last to y = zero")
        self.zeroButton.clicked.connect(self.zeroButton_clicked)

        self.startEndButton = QtGui.QPushButton(self)
        self.startEndButton.setText("add start/end")
        self.startEndButton.clicked.connect(self.startEndButton_clicked)

        self.le = QtGui.QLineEdit()
        self.le.setObjectName("bla")
        self.le.setText("")

        self.saveButton = QtGui.QPushButton(self)
        self.saveButton.setText("save")
        self.saveButton.clicked.connect(self.saveButton_clicked)

        self.sameHeightButton = QtGui.QPushButton(self)
        self.sameHeightButton.setText("set same height")
        self.sameHeightButton.clicked.connect(self.sameHeightButton_clicked)

        self.mergeButton = QtGui.QPushButton(self)
        self.mergeButton.setText("merge")
        self.mergeButton.clicked.connect(self.mergeButton_clicked)

        figure = mpl.figure.Figure()
        self.matplotlibWidget = MatplotlibWidget(figure)

        self.layoutVertical = QtGui.QVBoxLayout(self)
        self.layoutVertical.addWidget(self.pushButtonPlot)


        self.scroll = QtGui.QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setWidget(self.matplotlibWidget)

        self.layoutVertical.addWidget(self.scroll)


        self.layoutVertical.addWidget(self.removerButton)
        self.layoutVertical.addWidget(self.adderButton)
        self.layoutVertical.addWidget(self.zeroButton)
        self.layoutVertical.addWidget(self.startEndButton)
        self.layoutVertical.addWidget(self.le)
        self.layoutVertical.addWidget(self.saveButton)
        self.layoutVertical.addWidget(self.sameHeightButton)
        self.layoutVertical.addWidget(self.mergeButton)

    def removerButton_clicked(self):
        global mode
        mode = remove
        print "remover pressed"

    def adderButton_clicked(self):
        global mode
        mode = add
        print "add pressed"

    def startEndButton_clicked(self):
        global dots
        print "start end button pressed"
        dots.insert(0, [0,0])
        dots.append([self.matplotlibWidget.maxX,0])

        self.matplotlibWidget.waldoupdate()

    def zeroButton_clicked(self):
        global dots
        print "zero button pressed"
        if len(dots) >= 1:
            dots[0][1] = 0
            dots[len(dots)-1][1] = 0

        self.matplotlibWidget.waldoupdate()

    def saveButton_clicked(self):
        print "save button pressed, filename:", self.le.text()
        
        if self.le.text() and len(self.le.text()) > 0:
            # check if file exists already
            fname = folderName + '/' + self.le.text()
            if os.path.isfile(fname):
                backupname = folderName + '/trash/' + self.le.text() + '_' + strftime("%Y-%m-%d_%H_%M_%S")
                print 'file', fname, 'exists already, moving to', backupname
                shutil.move(fname, backupname)
            with open(fname, 'w') as f:
                for dot in plotdots:
                    f.write(str(dot[0]) + ': ' + str(int(dot[1])) + '\n')

        global dots, plotdots
        dots = []
        plotdots = []

        self.matplotlibWidget.initialize()

    def sameHeightButton_clicked(self):
        print "set same height button pressed, filename:", self.le.text()

        if len(dots) < 1:
            return

        global dots

        if self.le.text() and len(self.le.text()) > 0:

            try:

                if int(self.le.text()) not in self.matplotlibWidget.data:
                    print self.le.text(), "not found in data!"
                    return

                d = self.matplotlibWidget.data[int(self.le.text())]

            except ValueError:
                print "text not int"

            xs = [float(item[0]) for item in d]
            ys = [float(item[1]) for item in d]

            idx = takeClosest(xs, dots[0][0])
            dots[0] = [xs[idx], ys[idx]]

            idx = takeClosest(xs, dots[len(dots)-1][0])
            dots[len(dots)-1] = [xs[idx], ys[idx]]

            self.matplotlibWidget.waldoupdate()

    def mergeButton_clicked(self):
        global dots, plotdots
        print "merge button clicked"

        if len(dots) < 1:
            return


        if self.le.text() and len(self.le.text()) > 0:

            try:

                if int(self.le.text()) not in self.matplotlibWidget.data:
                    print self.le.text(), "not found in data!"
                    return

                d = self.matplotlibWidget.data[int(self.le.text())]

            except ValueError:
                print "text not int"

            xs = [float(item[0]) for item in d]
            ys = [float(item[1]) for item in d]

            nxs = [float(item[0]) for item in plotdots]
            nys = [float(item[1]) for item in plotdots]

            newdots = []

            x = 0.0
            i = 0

            while x < nxs[0]:
                newdots.append(d[i])
                x = xs[i]
                i += 1

            newdots.extend(plotdots)

            while x <= newdots[-1][0]:
                x = xs[i]
                i += 1

            newdots.extend(d[i:]) 

            plotdots = newdots

            self.matplotlibWidget.waldoupdate(interpolation=False)



    #@QtCore.pyqtSlot()
    def on_pushButtonPlot_clicked(self):
        global dots, plotdots
        print "erase pressed"
        dots = []
        plotdots = []

        self.matplotlibWidget.waldoupdate()


class ControlMainWindow(QtGui.QMainWindow):
    def __init__(self, foldername, parent=None):
        super(ControlMainWindow, self).__init__(parent)

        global folderName
        folderName = foldername

        

        self.setupUi()

    def setupUi(self):

        myWin = MyWindow()
        self.setCentralWidget(myWin)

        #figure = mpl.figure.Figure(figsize=(5, 5))
        #leftPlot = MatplotlibWidget(figure, data)
        #self.setCentralWidget(leftPlot)      

  
class MatplotlibWidget(FigureCanvasQTAgg):
    def __init__(self, fig):
        super(MatplotlibWidget, self).__init__(fig)


        self.figure = fig
        self.initialize()

        self.setFixedSize(self.maxX*200, 750)

        #---- setup event ----          

        self.mpl_connect('button_press_event', self.onclick)

    def initialize(self):
        data = loadFolder(folderName)

        self.data = data

        self.maxX = 0

        for k in self.data:
            x = [float(item[0]) for item in self.data[k]]
            self.maxX = max(max(x), self.maxX)

        self.waldoupdate()


    def waldoupdate(self, interpolation=True):
        self.waldodraw(interpolation)

        self.draw()

    def waldodraw(self, interpolation):
        if len(self.figure.axes) >= 1:
            ax = self.figure.axes[0]
            ax.cla()
        ax = self.figure.add_axes([0.1, 0.1, 0.85, 0.85])
        ax.set_ylim([0, 1300])
        for k in self.data:
            #print k
            x = [float(item[0]) for item in self.data[k]]
            y = [int(item[1]) for item in self.data[k]]
            ax.plot(x,y,label=str(k))

        if interpolation:
            interpol()

        if len(plotdots) >= 1:
            x = [float(item[0]) for item in plotdots]
            y = [int(item[1]) for item in plotdots]
            ax.plot(x,y, 'r-', linewidth=4.0)
        if len(dots) >= 1:
            x = [float(item[0]) for item in dots]
            y = [int(item[1]) for item in dots]
            ax.plot(x,y, 'ko')

        leg = ax.legend(loc=2, ncol=8, mode="expand", borderaxespad=0.)
        ax.xaxis.set_ticks(range(1,96))
        for legobj in leg.legendHandles:
            legobj.set_linewidth(3.0)

    def onclick(self, event):
        global dots

        x, y = event.x, event.y        
        print(event.xdata, event.ydata)

        if event.xdata == None or event.ydata == None:
            return

        if x != None and y != None:
            ydata = min(event.ydata, 1023)
            mode(event.xdata, ydata)
            self.waldodraw(interpolation=True)
            #ax.plot(event.xdata, event.ydata, 'ro')
            self.draw()


def loadFile(fname):
    with open(fname) as f:
        lines = f.read().splitlines() 
    datas = []
    for line in lines: 
        datas.append(line.split(': '))
    return datas


def loadFolder(name):

    ids = []
    for filename in os.listdir(name): 
        ids.append(filename)

    datas = {}
    for i in ids:
        fname = name + '/' + str(i)
        d = loadFile(fname)
        datas[i] = d
    return datas


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "need folder"
        sys.exit(0)

    app = QtGui.QApplication(sys.argv)
    mySW = ControlMainWindow(sys.argv[1])
    mySW.show()
    sys.exit(app.exec_())
