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
        self.serialObject = serial.Serial (port = nom_port, baudrate=57600, timeout =1)
        self.thread_ecoute = threading.Thread ( target=self.ecoute,)
        self.width = self.frameGeometry().width()
        self.height = self.frameGeometry().height()
        self.dist_dict = [0 for _ in range(360)]
        self.quality_dict = [0 for _ in range(360)]
        self.motorSpeed = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.repaint)
        self.timer.start(150)
        self.reset_timer = QTimer()
        self.reset_timer.timeout.connect(self.reset_dicts)
        self.reset_timer.start(3000)

    def closeEvent(self, event):
        self.stop()

    def reset_dicts(self):
        self.dist_dict = [0 for _ in range(360)]
        self.quality_dict = [0 for _ in range(360)]

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
            c = int(self.width/2 + dist/4*self.zoom*math.cos((angle - 90)/180*math.pi))
            d = int(self.height/2 + dist/4*self.zoom*math.sin((angle - 90)/180*math.pi))
            if self.quality_dict[angle] == 0:
                painter.setPen(QPen(QColor(200, 0, 0, alpha=5), 3))
                painter.drawLine(QPoint(a, b), QPoint(c, d))
            else:
                if dist > 3000:
                    painter.setPen(QPen(QColor(0, 0, 200, alpha=30), 3))
                else:
                    painter.setPen(QPen(QColor(0, 150, 0, alpha=30+self.quality_dict[angle]*3), 3))
                painter.drawLine(QPoint(a, b), QPoint(c, d))
        
    #Autres méthodes très utiles

    def ecoute (self):
        while self.listen:
            message = self.serialObject.readline ()
            message = message.decode ()
            if len (message) != 0:
                msg_s = message.split()
                #print(msg_s)
                if len(msg_s) >= 3:
                    try:
                        angle = int(float((msg_s[0])))
                        if angle < 360:
                            self.dist_dict[angle] = int(float(msg_s[1]))
                            self.quality_dict[angle] = int(float(msg_s[2]))
                            if len(msg_s) == 3:
                                print(angle, self.dist_dict[angle], self.quality_dict[angle])
                            else:
                                print(angle, self.dist_dict[angle], self.quality_dict[angle], msg_s[3])
                    except:
                        pass

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
