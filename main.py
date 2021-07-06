import sys
import serial
import threading
import math
import time
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QTimer, Qt, QRect, QPoint, pyqtSignal, QT_VERSION_STR
from PyQt5.QtGui import QBrush, QColor, QPainter, QFont, QPen

SEUIL_EXT = 300
SEUIL_INT = 375

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
        self.timer = QTimer()
        self.timer.timeout.connect(self.repaint)
        self.timer.start(150)
        self.data_counter = 0
        self.time_last_reset = time.time()
        self.proximity=[0, 0, 0, 0, 0, 0, "C"]
        self.last_proximity = time.time()
        self.reset_timer = QTimer()
        self.reset_timer.timeout.connect(self.reset_dicts)
        self.reset_timer.start(3000)

    def closeEvent(self, event):
        self.stop()

    def reset_dicts(self):
        self.data_counter = 0
        self.time_last_reset = time.time()
        self.dist_dict = [0 for _ in range(360)]
        self.quality_dict = [0 for _ in range(360)]
        if self.last_proximity > 1.900:
            self.proximity = [0, 0, 0, 0, 0, 0, "C"]

    def paintEvent(self, event):
        """Evt appellé à chaque fois que le widget est resize ou caché"""
        self.width = self.frameGeometry().width()
        self.height = self.frameGeometry().height()
        painter = QPainter(self)
        a = int(self.width/2)
        b = int(self.height/2)
        center = QPoint(a, b)
        #dessin forme robot
        #painter.drawRect(
        #dessin rayon lidar
        #
        #dessin orientation réelle robot
        #
        painter.drawEllipse(center, int(125*self.zoom), int(125*self.zoom)) #0.5m
        painter.drawText(QPoint(a+int(125*self.zoom), b+30), "0.5m")
        painter.drawEllipse(center, int(250*self.zoom), int(250*self.zoom)) #1m
        painter.drawText(QPoint(a+int(250*self.zoom), b+30), "1m")
        painter.drawEllipse(center, int(500*self.zoom), 500*self.zoom) #2m
        painter.drawText(QPoint(a+int(500*self.zoom), b+30), "2m")
        painter.drawEllipse(center, int(750*self.zoom), int(750*self.zoom)) #3m
        painter.drawText(QPoint(a+int(750*self.zoom), b+30), "3m")
        
        painter.setPen(QPen(QColor(200, 0, 0, alpha=127), 1))
        #dessin de la zone proximity_check externe avant
        c = int(self.width/2 + SEUIL_EXT/4*self.zoom*math.cos((-45 - 90)/180*math.pi))
        d = int(self.height/2 + SEUIL_EXT/4*self.zoom*math.sin((-45 - 90)/180*math.pi))
        painter.drawLine(QPoint(a, b), QPoint(c, d))
        c = int(self.width/2 + SEUIL_EXT/4*self.zoom*math.cos((45 - 90)/180*math.pi))
        d = int(self.height/2 + SEUIL_EXT/4*self.zoom*math.sin((45 - 90)/180*math.pi))
        painter.drawLine(QPoint(a, b), QPoint(c, d))
        #zone externe arrière
        c = int(self.width/2 + SEUIL_EXT/4*self.zoom*math.cos((-45+180 - 90)/180*math.pi))
        d = int(self.height/2 + SEUIL_EXT/4*self.zoom*math.sin((-45+180 - 90)/180*math.pi))
        painter.drawLine(QPoint(a, b), QPoint(c, d))
        c = int(self.width/2 + SEUIL_EXT/4*self.zoom*math.cos((45+180 - 90)/180*math.pi))
        d = int(self.height/2 + SEUIL_EXT/4*self.zoom*math.sin((45+180 - 90)/180*math.pi))
        painter.drawLine(QPoint(a, b), QPoint(c, d))
        #dessin arc entre externe et interne
        #avant
        painter.drawArc(a-SEUIL_EXT/4*self.zoom, b-SEUIL_EXT/4*self.zoom, 2*SEUIL_EXT/4*self.zoom, 2*SEUIL_EXT/4*self.zoom, 45*16, 25*16)
        painter.drawArc(a-SEUIL_EXT/4*self.zoom, b-SEUIL_EXT/4*self.zoom, 2*SEUIL_EXT/4*self.zoom, 2*SEUIL_EXT/4*self.zoom, 110*16, 25*16)
        #arrière
        painter.drawArc(a-SEUIL_EXT/4*self.zoom, b-SEUIL_EXT/4*self.zoom, 2*SEUIL_EXT/4*self.zoom, 2*SEUIL_EXT/4*self.zoom, (45+180)*16, 25*16)
        painter.drawArc(a-SEUIL_EXT/4*self.zoom, b-SEUIL_EXT/4*self.zoom, 2*SEUIL_EXT/4*self.zoom, 2*SEUIL_EXT/4*self.zoom, (110+180)*16, 25*16)
        
        #dessin arc entre externe et interne
        #avant
        painter.drawArc(a-SEUIL_INT/4*self.zoom, b-SEUIL_INT/4*self.zoom, 2*SEUIL_INT/4*self.zoom, 2*SEUIL_INT/4*self.zoom, 70*16, 40*16)
        painter.drawArc(a-SEUIL_INT/4*self.zoom, b-SEUIL_INT/4*self.zoom, 2*SEUIL_INT/4*self.zoom, 2*SEUIL_INT/4*self.zoom, 250*16, 40*16)
        
        #dessin limites latératles zone interne avant
        pa = int(self.width/2 + SEUIL_EXT/4*self.zoom*math.cos((-20 - 90)/180*math.pi))
        pb = int(self.height/2 + SEUIL_EXT/4*self.zoom*math.sin((-20 - 90)/180*math.pi))
        c = int(self.width/2 + SEUIL_INT/4*self.zoom*math.cos((-20 - 90)/180*math.pi))
        d = int(self.height/2 + SEUIL_INT/4*self.zoom*math.sin((-20 - 90)/180*math.pi))
        painter.drawLine(QPoint(pa, pb), QPoint(c, d))
        pa = int(self.width/2 + SEUIL_EXT/4*self.zoom*math.cos((20 - 90)/180*math.pi))
        pb = int(self.height/2 + SEUIL_EXT/4*self.zoom*math.sin((20 - 90)/180*math.pi))
        c = int(self.width/2 + SEUIL_INT/4*self.zoom*math.cos((20 - 90)/180*math.pi))
        d = int(self.height/2 + SEUIL_INT/4*self.zoom*math.sin((20 - 90)/180*math.pi))
        painter.drawLine(QPoint(pa, pb), QPoint(c, d))
        
        #dessin limites latératles zone interne arrière
        pa = int(self.width/2 + SEUIL_EXT/4*self.zoom*math.cos((-20+180 - 90)/180*math.pi))
        pb = int(self.height/2 + SEUIL_EXT/4*self.zoom*math.sin((-20+180 - 90)/180*math.pi))
        c = int(self.width/2 + SEUIL_INT/4*self.zoom*math.cos((-20+180 - 90)/180*math.pi))
        d = int(self.height/2 + SEUIL_INT/4*self.zoom*math.sin((-20+180 - 90)/180*math.pi))
        painter.drawLine(QPoint(pa, pb), QPoint(c, d))
        pa = int(self.width/2 + SEUIL_EXT/4*self.zoom*math.cos((20+180 - 90)/180*math.pi))
        pb = int(self.height/2 + SEUIL_EXT/4*self.zoom*math.sin((20+180 - 90)/180*math.pi))
        c = int(self.width/2 + SEUIL_INT/4*self.zoom*math.cos((20+180 - 90)/180*math.pi))
        d = int(self.height/2 + SEUIL_INT/4*self.zoom*math.sin((20+180 - 90)/180*math.pi))
        painter.drawLine(QPoint(pa, pb), QPoint(c, d))
        
        painter.setPen(Qt.red)
        painter.drawText(QPoint(30, 30), "Nombre de points {} en {}s".format(self.data_counter, str(time.time()-self.time_last_reset)[:5]))
        painter.drawText(QPoint(30, 40), "0° vers le haut, 90° vers la droite")
        
        for angle, dist in enumerate(self.dist_dict):
            c = int(self.width/2 + dist/4*self.zoom*math.cos((angle - 90)/180*math.pi))
            d = int(self.height/2 + dist/4*self.zoom*math.sin((angle - 90)/180*math.pi))
            if self.quality_dict[angle] == 0:
                painter.setPen(QPen(QColor(200, 0, 0, alpha=5), 3))
                painter.drawLine(QPoint(a, b), QPoint(c, d))
            else:
                if dist > 3000:
                    painter.setPen(QPen(QColor(0, 0, 200, alpha=10), 3))
                else:
                    painter.setPen(QPen(QColor(0, 150, 0, alpha=50+self.quality_dict[angle]*0.01), 3))
                painter.drawLine(QPoint(a, b), QPoint(c, d))
        c = int(self.width/2 + self.proximity[1]/4*self.zoom*math.cos((self.proximity[0] - 90)/180*math.pi))
        d = int(self.height/2 + self.proximity[1]/4*self.zoom*math.sin((self.proximity[0] - 90)/180*math.pi))
        
        if self.proximity[6] == "P":
            painter.setPen(QPen(QColor(200, 0, 0, alpha=255), 3))
        else:
            painter.setPen(QPen(QColor(0, 200, 0, alpha=255), 3))
        painter.drawLine(QPoint(a, b), QPoint(c, d))
        painter.drawText(QPoint(c-150, d), "PROXIMITY {}° {}mm q{} pt({}, {}) {}ms ago".format(self.proximity[0], self.proximity[1], self.proximity[2], self.proximity[3], self.proximity[4], self.proximity[5]))
        
    #Autres méthodes très utiles

    def ecoute (self):
        while self.listen:
            message = self.serialObject.readline ()
            message = message.decode ()
            if len (message) != 0:
                msg_s = message.split()
                #print(msg_s)
                if len(msg_s) == 3:
                    try:
                        angle = int(float((msg_s[0])))
                        if angle < 360:
                            self.data_counter += 1
                            self.dist_dict[angle] = int(float(msg_s[1]))
                            self.quality_dict[angle] = int(float(msg_s[2]))
                            if len(msg_s) == 3:
                                print(angle, self.dist_dict[angle], self.quality_dict[angle])
                            else:
                                print(angle, self.dist_dict[angle], self.quality_dict[angle], msg_s[3])
                    except:
                        pass
                elif len(msg_s) == 8 and msg_s[0] == "p":
                    print(message)
                    self.proximity = [int(msg_s[1]), float(msg_s[2]), int(msg_s[3]), float(msg_s[4]), float(msg_s[5]), float(msg_s[6]), str(msg_s[7])]
                    self.last_proximity = time.time()
                elif len(msg_s) == 2 and message=="p C":
                    self.proximity = [0, 0, 0, 0, 0, 0, "C"]
                    self.last_proximity = time.time()

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
