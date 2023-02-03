from PyQt5 import QtCore, QtGui, QtWidgets, QtSerialPort
from pyqtgraph import PlotWidget, plot
from pyqtgraph.metaarray.MetaArray import axis

from MainWindow import *
from UART import *

import pyqtgraph as pg
import serial
import math
import sys
import os

class GUI(Ui_MainWindow):

    def __init__(self, MainWindow) -> None:
        super(GUI, self).__init__()
        self.setupUi(MainWindow)
        self.init_variable()
        self.init_default_config_window()
        self.init_callback()

    def init_variable(self):
        self.uart = UARTQThread()
        self.checkMode:int = 10

        self.penVar = pg.mkPen(color=(255, 0, 0), width=3)
        self.penSP = pg.mkPen(color=(0, 0, 255), width=2)
        self.styles = {"color": "#191970", "font-size": "20px"}

        self.timeBuff:list = [0]
        self.varBuff:list = [0]
        self.setpointBuff:list = [0]
        self.setpointData:int = 0
        self.PIDSendData:str = ""
        self.T_samp:float = 0.03

    def init_default_config_window(self):
        self.label_6.setPixmap(QtGui.QPixmap("src\\../Image/Logo.png"))
        self.Connect_but.setStyleSheet("QPushButton {color: green;}")
        self.Start_but.setStyleSheet("QPushButton"
                                 "{"
                                 "background-color : lightgreen;"
                                 "}"
                                 "QPushButton::pressed"
                                 "{"
                                 "background-color : green;"
                                 "}")
        self.Stop_but.setStyleSheet("QPushButton"
                                "{"
                                "background-color : #FAA0A0;"
                                "}"
                                "QPushButton::pressed"
                                "{"
                                "background-color : red;"
                                "}")
        self.Reset_but.setStyleSheet("QPushButton"
                                "{"
                                "background-color : lightyellow;"
                                "}"
                                "QPushButton::pressed"
                                "{"
                                "background-color : yellow;"
                                "}")  
        self.getPID_but.setStyleSheet("QPushButton"
                                    "{"
                                    "background-color : #DCDCDC;"
                                    "}"
                                    "QPushButton::pressed"
                                    "{"
                                    "background-color : #808080;"
                                    "}")   
        self.sendPID_but.setStyleSheet("QPushButton"
                                    "{"
                                    "background-color : #DCDCDC;"
                                    "}"
                                    "QPushButton::pressed"
                                    "{"
                                    "background-color : #808080;"
                                    "}")

        self.Velocity_but.setStyleSheet("QPushButton" "{" "background-color : #DCDCDC;" "}")
        self.Position_but.setStyleSheet("QPushButton" "{" "background-color : #DCDCDC;" "}")

        # set up Position_graph
        self.Position_graph.setBackground("#d5ecf2")
        self.Position_graph.showGrid(x=True, y=True)
        self.Position_graph.setMouseEnabled(x=False, y=False)
        self.Position_graph.setLabel("left", "Corner(degree)", **self.styles)
        self.Position_graph.setLabel("bottom", "Time(s)", **self.styles)

        # set up Velocity_graph
        self.Velocity_graph.setBackground("#d5ecf2")
        self.Velocity_graph.showGrid(x=True, y=True)
        self.Velocity_graph.setMouseEnabled(x=False, y=False)
        self.Velocity_graph.setLabel("left", "Velocity(rpm)", **self.styles)
        self.Velocity_graph.setLabel("bottom", "Time(s)", **self.styles)

        # disable button, box
        self.Start_but.setEnabled(False)
        self.Stop_but.setEnabled(False)
        self.Reset_but.setEnabled(False)
        self.sendPID_but.setEnabled(False)

    def plotGrap(self):
        self.timeBuff.append(len(self.varBuff) * self.T_samp)
        self.setpointBuff.append(float(self.setpointData))

        if self.checkMode == 1:
            self.Velocity_graph.clear()
            self.Velocity_graph.plot(self.timeBuff, self.varBuff, pen=self.penVar)
            self.Velocity_graph.plot(self.timeBuff, self.setpointBuff, pen=self.penSP)
        elif self.checkMode == 2:
            self.Position_graph.clear()
            self.Position_graph.plot(self.timeBuff, self.varBuff, pen=self.penVar)
            self.Position_graph.plot(self.timeBuff, self.setpointBuff, pen=self.penSP)

    def init_callback(self):
        self.Connect_but.clicked.connect(self.clickedConnectCallback)
        self.Start_but.clicked.connect(self.clickedStartCallback)
        self.Stop_but.clicked.connect(self.clickedStopCallback)
        self.Reset_but.clicked.connect(self.clickedResetCallBack)
        self.getPID_but.clicked.connect(self.clickedGetPIDCallback)
        self.sendPID_but.clicked.connect(self.clickedSendPIDCallback)
        self.Velocity_but.clicked.connect(self.clickedVelocityCallback)
        self.Position_but.clicked.connect(self.clickedPositionCallback)

        self.uart.getByteData.connect(self.getByteDataCallback)
        self.uart.getByteControl.connect(self.getByteControlCallback)
        self.uart.getBytePIDPar.connect(self.getBytePIDParCallback)

    def clickedConnectCallback(self):
        NameCOM = self.COM.currentText()
        try:
            if self.uart.stateConnect() == False:
                self.uart.Connect(nameCOM= NameCOM, baud= 115200)
                self.uart.start()
                self.COM.setEnabled(False)
                self.Start_but.setEnabled(True)
                self.Stop_but.setEnabled(True)
                self.Reset_but.setEnabled(True)
                self.sendPID_but.setEnabled(True)
                self.Connect_but.setText("DISCONNECT")
                self.Connect_but.setStyleSheet("QPushButton {color: red;}")
                self.note.append("Serial port " + NameCOM + " opened")
            else:
                self.uart.terminate()
                self.uart.disConnect()
                self.COM.setEnabled(True)
                self.Start_but.setEnabled(False)
                self.Stop_but.setEnabled(False)
                self.Reset_but.setEnabled(False)
                self.sendPID_but.setEnabled(False)
                self.Connect_but.setText("CONNECT")
                self.Connect_but.setStyleSheet("QPushButton {color: green;}")
                self.note.append("Serial port " + NameCOM + " closed" + "\n")
        except IOError:
            if self.uart.stateConnect() == False:
                self.note.append("Serial port " + NameCOM + " opening error" + "\n")
            else:
                self.note.append("Serial port " + NameCOM + " closing error" + "\n")

    def clickedStartCallback(self):
        if self.checkMode == 10:
            self.note.append("Choose Mode" + "\n")
        else:
            if self.checkMode == 0:
                strs_tmp = ["0", "0", "0", "\n"]
            elif self.checkMode == 1:
                strs_tmp = ["0", "0", "1", "\n"]
            else:
                strs_tmp = ["0", "0", "2", "\n"]
            startDataSend = " ".join(strs_tmp)
            self.uart.transmit(startDataSend)
    
    def clickedStopCallback(self):
        strs_tmp = ["0", "1", "0", "\n"]
        stopDataSend = " ".join(strs_tmp)
        self.uart.transmit(stopDataSend)

    def clickedResetCallBack(self):
        strs_tmp = ["0", "2", "0", "\n"]
        resetdataSend = " ".join(strs_tmp)
        self.uart.transmit(resetdataSend)

        self.Position_graph.clear()
        self.Position_graph.setYRange(0, 1, padding=0)
        self.Velocity_graph.clear()
        self.Velocity_graph.setYRange(0, 1, padding=0)
        self.varBuff = [0]
        self.timeBuff = [0]
        self.setpointBuff = [0]

        self.checkMode = 10
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.Velocity_but.setFont(font)
        self.Velocity_but.setStyleSheet("QPushButton" "{" "background-color : #DCDCDC;" "}")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.Position_but.setFont(font)
        self.Position_but.setStyleSheet("QPushButton" "{" "background-color : #DCDCDC;" "}")

    def clickedGetPIDCallback(self):
        try:
            strs_tmp = [
                "1",
                self.Kp_data.toPlainText(),
                self.Ki_data.toPlainText(),
                self.Kd_data.toPlainText(),
                self.Setpoint_data.toPlainText(),
                "\n",
            ]
            self.PIDSendData = " ".join(strs_tmp)
            self.setpointData = self.Setpoint_data.toPlainText()
        except:
            self.note.append("The only allowed PID parameter is the REAL NUMBER" + "\n")

    def clickedSendPIDCallback(self):
        self.uart.transmit(self.PIDSendData)

    def clickedVelocityCallback(self):
        self.checkMode = 1
        self.note.append("You choose control velocity" + "\n")
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.Velocity_but.setFont(font)
        self.Velocity_but.setStyleSheet("QPushButton" "{" "background-color : #0000FF;" "}")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.Position_but.setFont(font)
        self.Position_but.setStyleSheet("QPushButton" "{" "background-color : #DCDCDC;" "}")
        if int(self.Setpoint_data.toPlainText()) < 0:
            self.Velocity_graph.setYRange(-300, 0, padding=0)
        else:
            self.Velocity_graph.setYRange(0, 300, padding=0)

    def clickedPositionCallback(self):
        self.checkMode = 2
        self.note.append("You choose control position" + "\n")
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.Position_but.setFont(font)
        self.Position_but.setStyleSheet("QPushButton" "{" "background-color : #0000FF;" "}")
        font.setPointSize(9)
        font.setBold(False)
        font.setWeight(50)
        self.Velocity_but.setFont(font)
        self.Velocity_but.setStyleSheet("QPushButton" "{" "background-color : #DCDCDC;" "}")
        if int(self.Setpoint_data.toPlainText()) < 0:
            if int(self.Setpoint_data.toPlainText()) > -500:
                self.Position_graph.setYRange(-700, 0, padding=0)
            elif int(self.Setpoint_data.toPlainText()) > -1000:
                self.Position_graph.setYRange(-1400, 0, padding=0)
            else:
                self.Position_graph.setYRange(-2400, 0, padding=0)
        else:
            if int(self.Setpoint_data.toPlainText()) < 500:
                self.Position_graph.setYRange(0, 700, padding=0)
            elif int(self.Setpoint_data.toPlainText()) < 1000:
                self.Position_graph.setYRange(0, 1400, padding=0)
            else:
                self.Position_graph.setYRange(0, 2400, padding=0)

    def getByteDataCallback(self, RXDataBuff:list):
        self.varBuff.append(float(str(RXDataBuff[1], "UTF-8")))
        self.re_se_data.append("value = "
                                + str(RXDataBuff[1], "UTF-8")
                                + "        "
                                + "u_control = "
                                + str(RXDataBuff[2], "UTF-8")
                            )
        self.plotGrap()
    
    def getByteControlCallback(self, RXDataBuff:list):
        if int(float(str(RXDataBuff[1], "UTF-8"))) == 0:
            self.note.append("Motor is running" + "\n")
        elif int(float(str(RXDataBuff[1], "UTF-8"))) == 1:
            self.note.append("Motor has been stopped" + "\n")
        else:
            self.re_se_data.clear()
            self.note.clear()
            self.note.append("System has been resetted" + "\n")

    def getBytePIDParCallback(self, RXDataBuff:list):
        self.note.append("Please check again your PID parameters!")
        self.note.append("PID parameter you send is:"
                        + "\n"
                        + "  Kp = "
                        + str(RXDataBuff[1], "UTF-8")
                        + "\n"
                        + "  Ki = "
                        + str(RXDataBuff[2], "UTF-8")
                        + "\n"
                        + "  Kd = "
                        + str(RXDataBuff[3], "UTF-8")
                        + "\n"
                        + "  Setpoint = "
                        + str(RXDataBuff[4], "UTF-8")
                        + "\n"
                    )

def UIbuild():
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = GUI(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    UIbuild()