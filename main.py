from PyQt5 import QtCore
from PyQt5.QtCore import QIODevice, pyqtSignal
from PyQt5.QtWidgets import *
from pid_controller import Ui_MainWindow
import sys, serial
import pyqtgraph as pg
import numpy as np
from time import sleep


class SerialThread(QtCore.QThread):

    message = pyqtSignal(str)

    def __init__(self, data):
        self.data = data
        QtCore.QThread.__init__(self)
        self.port = serial.Serial('COM3', 9600)
        self.running = True

    def run(self):
        while self.running:
            self.read()

    def send(self, data):
        self.port.write(data)

    def read(self):
        self.data = self.port.readline().decode().strip('\r\n')
        self.message.emit(str(self.data))


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.graphWidget = pg.GraphicsLayoutWidget(show=True, parent=self.ui.GraphWidget)
        self.ui.graphWidget.setGeometry(QtCore.QRect(0, 0, 500, 300))
        self.plt = self.ui.graphWidget.addPlot()
        self.arr_data = ''
        self.serial_th = SerialThread(self.arr_data)
        self.serial_th.message.connect(self.showValues)
        self.ui.start_stop_button.start = True
        self.ui.start_stop_button.stop = False
        self.ui.start_stop_button.setStyleSheet("background-color: green")
        self.ui.start_stop_button.setText("ЗАП.")
        self.ui.start_stop_button.clicked.connect(self.StartStopPlot)
        self.ui.input_button.clicked.connect(self.SendData)
        self.serial_th.start()
        sleep(2)

        self.timer = QtCore.QTimer(self)

        self.timer.setInterval(10)
        self.timer.start()
        self.timer.timeout.connect(self.onNewData)
        self.i = 0
        self.x = np.array([])
        self.y = np.array([])
        self.curve = self.plt.plot(self.x, self.y)
        self.curve.setPen((255,0,0))
        self.line = pg.InfiniteLine(movable=False, angle=0, pen=(0,0,255))
        self.plt.addItem(self.line)


    def showValues(self):
        self.ui.meas_val.display(self.serial_th.data.split(" ")[0])
        self.ui.err_val.display(float(self.serial_th.data.split(" ")[1]) - float(self.serial_th.data.split(" ")[0]))

    def onNewData(self):
        self.x = np.append(self.x, self.timer.interval() * self.i)
        try:
            self.y = np.append(self.y, float(self.serial_th.data.split(" ")[0]))
        except:
            self.y = np.append(self.y, 0)
        if len(self.x) > 100000:
            self.x = self.x[1:]
            self.y = self.y[1:]
        self.curve.setData(self.x, self.y)
        self.i += 1
        self.line.setPos(float(self.serial_th.data.split(" ")[1]))

    def StartStopPlot(self):
        if self.ui.start_stop_button.start:
            self.ui.start_stop_button.start = False
            self.ui.start_stop_button.stop = True
            self.ui.start_stop_button.setStyleSheet("background-color: red")
            self.ui.start_stop_button.setText("ОСТ.")
            self.timer.stop()
        else:
            self.ui.start_stop_button.start = True
            self.ui.start_stop_button.stop = False
            self.ui.start_stop_button.setStyleSheet("background-color: green")
            self.ui.start_stop_button.setText("ЗАП.")
            self.timer.start()

    def SendData(self):
        sp = self.ui.setpoint_line.text()
        Kp = self.ui.P_edit.text()
        Ki = self.ui.I_edit.text()
        Kd = self.ui.D_edit.text()
        if sp != '':
            self.serial_th.send(f's{float(sp)}'.encode('utf-8'))
        if Kp != '':
            self.serial_th.send(f'p{float(Kp)}'.encode('utf-8'))
        if Ki != '':
            self.serial_th.send(f'i{float(Ki)}'.encode('utf-8'))
        if Kd != '':
            self.serial_th.send(f'd{float(Kd)}'.encode('utf-8'))



if __name__ == "__main__":
    pg.setConfigOption('background', 'w')
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())