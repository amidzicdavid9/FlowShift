import scapy.all as scapy
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDoubleSpinBox,
    QFontComboBox,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

import sys



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")

        button = QPushButton("Press Me!")
        button.setCheckable(True)
        button.clicked.connect(self.the_button_was_clicked)
        button.clicked.connect(self.the_button_was_toggled)

        self.setMinimumSize(QSize(400, 300))
        self.setMaximumSize(QSize(1200, 900))
        self.setCentralWidget(button)

    def the_button_was_clicked(self):
        p = scapy.sr(scapy.IP(dst="www.google.com") / scapy.ICMP() / "XXXXXXXXXXX")
        print("Clicked!")

    def the_button_was_toggled(self, checked):
        print("Checked?", checked)


p = scapy.IP()




app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()


