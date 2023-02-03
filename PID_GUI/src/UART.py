import serial
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QElapsedTimer,QThread, QObject, pyqtSignal as Signal, pyqtSlot as Slot

class UARTQThread(QThread):
    getByteData = Signal(list)
    getByteControl = Signal(list)
    getBytePIDPar = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.ser = serial.Serial
        self.COMName: str = ""
        self.COMConnect: bool = False
        self.RXdataBuff: list =[]

    def stateConnect(self) -> bool:
        return self.COMConnect

    def Connect(self, nameCOM:str,baud:int):
        self.ser = serial.Serial(nameCOM,baudrate=baud, timeout=0.1)
        self.COMConnect = True

    def disConnect(self):
        self.ser.close()
        self.COMConnect = False

    def transmit(self, DataSend:str):
        self.ser.write(DataSend.encode())

    def recive(self):
        RXdata = self.ser.readline()
        self.RXdataBuff = RXdata.split()
    
    def processData(self):
        if int(float(str(self.RXdataBuff[0], "UTF-8"))) == 0:
            self.getByteData.emit(self.RXdataBuff)
        elif int(float(str(self.RXdataBuff[0], "UTF-8"))) == 1:
            self.getByteControl.emit(self.RXdataBuff)
        else:
            self.getBytePIDPar.emit(self.RXdataBuff)

    @Slot()
    def run(self):
        while (self.COMConnect):
            bytetoRead = self.ser.inWaiting()
            if bytetoRead > 0:
                self.recive()
                self.processData()


