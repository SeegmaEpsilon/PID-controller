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
        self.cursor_x1 = pg.InfiniteLine(movable=True, angle=90, label='x1', pen=(255, 0, 255),
                       labelOpts={'position': 0.1, 'color': (255, 0, 255), 'fill': (255, 0, 255,50), 'movable': True})
        self.cursor_x2 = pg.InfiniteLine(movable=True, angle=90, label='x2', pen=(255, 0, 255),
                                         labelOpts={'position': 0.1, 'color': (255, 0, 255), 'fill': (255, 0, 255, 50),
                                                    'movable': True})
        self.cursor_y1 = pg.InfiniteLine(movable=True, angle=0, label='y1', pen=(0, 128, 0),
                                         labelOpts={'position': 0.1, 'color': (0, 128, 0), 'fill': (0, 128, 0, 50),
                                                    'movable': True})
        self.cursor_y2 = pg.InfiniteLine(movable=True, angle=0, label='y2', pen=(0, 128, 0),
                                         labelOpts={'position': 0.1, 'color': (0, 128, 0), 'fill': (0, 128, 0, 50),
                                                    'movable': True})
        self.plt.addItem(self.cursor_x1)
        self.plt.addItem(self.cursor_x2)
        self.plt.addItem(self.cursor_y1)
        self.plt.addItem(self.cursor_y2)
        self.cursor_x1.sigPositionChanged.connect(self.cursor_position_changed)
        self.cursor_x2.sigPositionChanged.connect(self.cursor_position_changed)
        self.cursor_y1.sigPositionChanged.connect(self.cursor_position_changed)
        self.cursor_y2.sigPositionChanged.connect(self.cursor_position_changed)
        self.ui.delta_X_button.on = False
        self.ui.delta_Y_button.on = False
        self.ui.delta_X_button.clicked.connect(self.cursor_X_visible)
        self.ui.delta_Y_button.clicked.connect(self.cursor_Y_visible)
        self.cursor_x1.hide()
        self.cursor_x2.hide()
        self.cursor_y1.hide()
        self.cursor_y2.hide()
        self.ui.label_delta_X.hide()
        self.ui.label_delta_Y.hide()
        self.ui.delta_X_LCD.hide()
        self.ui.delta_Y_LCD.hide()


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

    def cursor_X_visible(self):
        if not self.ui.delta_X_button.on:
            self.ui.delta_X_button.on = True
            self.ui.label_delta_X.show()
            self.ui.delta_X_LCD.show()
            view_range = self.plt.viewRange()
            self.ui.delta_X_button.setStyleSheet("background-color: green")
            self.cursor_x1.setPos(view_range[0][0] + (view_range[0][1] - view_range[0][0]) / 2)
            self.cursor_x2.setPos(view_range[0][0] + (view_range[0][1] - view_range[0][0]) / 4)
            self.cursor_x1.show()
            self.cursor_x2.show()

        else:
            self.ui.delta_X_button.on = False
            self.ui.label_delta_X.hide()
            self.ui.delta_X_LCD.hide()
            self.ui.delta_X_button.setStyleSheet("background-color: red")
            self.cursor_x1.hide()
            self.cursor_x2.hide()

    def cursor_Y_visible(self):
        if not self.ui.delta_Y_button.on:
            self.ui.delta_Y_button.on = True
            self.ui.label_delta_Y.show()
            self.ui.delta_Y_LCD.show()
            view_range = self.plt.viewRange()
            self.ui.delta_Y_button.setStyleSheet("background-color: green")
            self.cursor_y1.setPos(self.line.getPos()[1] * 0.95)
            self.cursor_y2.setPos(self.line.getPos()[1] * 1.05)
            self.cursor_y1.show()
            self.cursor_y2.show()

        else:
            self.ui.delta_Y_button.on = False
            self.ui.label_delta_Y.hide()
            self.ui.delta_Y_LCD.hide()
            self.ui.delta_Y_button.setStyleSheet("background-color: red")
            self.cursor_y1.hide()
            self.cursor_y2.hide()


    def cursor_position_changed(self):
        x1 = self.cursor_x1.getPos()[0]
        x2 = self.cursor_x2.getPos()[0]
        y1 = self.cursor_y1.getPos()[1]
        y2 = self.cursor_y2.getPos()[1]
        delta_x = round(abs(x1 - x2), 1)
        delta_y = round(abs(y1 - y2), 2)
        self.ui.delta_X_LCD.display(delta_x)
        self.ui.delta_Y_LCD.display(delta_y)


    def switch_mode(self):
        self.x = np.array([])
        self.y = np.array([])



if __name__ == "__main__":
    pg.setConfigOption('background', 'w')
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())