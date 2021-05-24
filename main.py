import sys
import serial
import threading
import math
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QTimer, Qt, QRect, QPoint, pyqtSignal, QT_VERSION_STR
from PyQt5.QtGui import QBrush, QColor, QPainter, QFont, QPen

class OutilDiagnostic(QWidget):
    def __init__(self, nom_port, zoom=1):
        super().__init__()
        self.resize(600, 700)
        self.listen = True 
        self.zoom = zoom
        self.serialObject = serial.Serial (port = nom_port, baudrate=115200, timeout =1)
        self.thread_ecoute = threading.Thread ( target=self.ecoute,)
        self.width = self.frameGeometry().width()
        self.height = self.frameGeometry().height()
        self.dist_dict = [0 for _ in range(360)]
        self.valid_dict = [0 for _ in range(360)]
        self.inzone_dict = [0 for _ in range(360)]
        self.true_pos = [[0, 0] for _ in range(360)]
        self.motorSpeed = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.repaint)
        self.timer.start(150)

    def closeEvent(self, event):
        self.stop()

    def paintEvent(self, event):
        """Evt appellé à chaque fois que le widget est resize ou caché"""
        self.width = self.frameGeometry().width()
        self.height = self.frameGeometry().height()
        painter = QPainter(self)
        a = int(self.width/2)
        b = int(self.height/2)
        center = QPoint(a, b)
        painter.drawEllipse(center, int(125*self.zoom), int(125*self.zoom)) #0.5m
        painter.drawText(QPoint(a+int(125*self.zoom), b+30), "0.5m")
        painter.drawEllipse(center, int(250*self.zoom), int(250*self.zoom)) #1m
        painter.drawText(QPoint(a+int(250*self.zoom), b+30), "1m")
        painter.drawEllipse(center, int(500*self.zoom), 500*self.zoom) #2m
        painter.drawText(QPoint(a+int(500*self.zoom), b+30), "2m")
        painter.drawEllipse(center, int(750*self.zoom), int(750*self.zoom)) #3m
        painter.drawText(QPoint(a+int(750*self.zoom), b+30), "3m")
        painter.setPen(Qt.red)
        painter.drawText(QPoint(30, 30), "MotorSpeed: {}".format(self.motorSpeed))
        painter.drawText(QPoint(30, 40), "0° vers le haut, 90° vers la gauche")
        for angle, dist in enumerate(self.dist_dict):
            c = int(self.width/2 - dist/4*self.zoom*math.cos((angle - 90)/180*math.pi))
            d = int(self.height/2 + dist/4*self.zoom*math.sin((angle - 90)/180*math.pi))
            if self.valid_dict[angle]:
                if self.inzone_dict[angle]:
                    painter.setPen(QPen(Qt.blue, 3))
                else:
                    painter.setPen(QPen(Qt.red, 3))
                painter.drawPoint(QPoint(c, d))
            else:
                painter.setPen(QPen(QColor(0, 0, 0, alpha=100), 3))
                c = int(self.width/2 - 1000/4*self.zoom*math.cos((angle - 90)/180*math.pi))
                d = int(self.height/2 + 1000/4*self.zoom*math.sin((angle - 90)/180*math.pi))
                painter.drawLine(QPoint(a, b), QPoint(c, d))
            if angle%8 == 0 and self.valid_dict[angle]:
                painter.drawText(QPoint(c, d), "{}: {}, {}".format(
                    angle, self.true_pos[angle][0], self.true_pos[angle][1]))
                painter.drawText(QPoint(c, d + 10), "{}, {}".format(
                    int(1500 + dist*math.cos(angle/180*math.pi)), int(1000 + dist*math.sin(angle/180*math.pi))))
        
    #Autres méthodes très utiles

    def ecoute (self):
        while self.listen:
            message = self.serialObject.readline ()
            message = message.decode ()
            if len (message) != 0:
                msg_s = message.split()
                print(msg_s)
                corrupt = False
                # for elt in msg_s[1:]:
                #     if corrupt:
                #         print("corrupt:", elt)
                #     corrupt = corrupt or not elt.isdecimal()
                if message[0] == "l" and not corrupt:
                    if len(msg_s) == 7:
                        angle = int(msg_s[1])
                        if angle <360:
                            self.dist_dict[angle] = int(msg_s[2])
                            self.valid_dict[angle] = int(msg_s[3])
                            self.inzone_dict[angle] = int(msg_s[4])
                            self.true_pos[angle] = [int(msg_s[5]), int(msg_s[6])]
                            #print(msg_s)
                elif message[0] == "s":
                    if len(msg_s) == 2:
                        self.motorSpeed = float(msg_s[1])

    def start (self):
        """Démarre le thread d'écoute"""
        self.thread_ecoute.start()

    def stop (self, *args):
        """Appelé automatiquement à l'arrêt du programme. 
        Met la condition de bouclage du thread d'écoute à False"""
        self.listen = False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    if len(sys.argv) > 2:
        ex = OutilDiagnostic(sys.argv[1], int(sys.argv[2])/100)
    else:
        ex = OutilDiagnostic(sys.argv[1])
    ex.start()
    ex.show()
    sys.exit(app.exec_())