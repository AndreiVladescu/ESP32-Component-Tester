import sys
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QCheckBox, QWidget, \
    QInputDialog, QDialog, QLineEdit, QFormLayout
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QMutex, QWaitCondition
import serial
import serial.tools.list_ports
import base64
import pickle
import os


class SerialThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)
        self.dummy_mode = True
        self.serial_port = None
        self.mutex = QMutex()
        self.condition = QWaitCondition()
        self.should_run = True

    def run(self):
        while self.should_run:
            if self.dummy_mode:
                data = str(random.randint(0, 100))
            else:
                if self.serial_port is not None:
                    data = self.serial_port.readline().decode('utf-8').strip()
                else:
                    data = "No serial port selected"
            self.signal.emit(data)
            self.mutex.lock()
            self.condition.wait(self.mutex, 1000)  # Wait for 1 second or until stopped
            self.mutex.unlock()

    def send_data(self, data):
        if not self.dummy_mode and self.serial_port is not None:
            self.serial_port.write(data.encode())

    def set_dummy_mode(self, dummy_mode):
        self.dummy_mode = dummy_mode

    def set_serial_port(self, port):
        if self.serial_port is not None:
            self.serial_port.close()
        self.serial_port = serial.Serial(port, 115200)

    def stop(self):
        self.mutex.lock()
        self.should_run = False
        self.condition.wakeAll()
        self.mutex.unlock()


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.ui_init()

        self.serial_init()

        self.credentials_file = ".cache"

    def ui_init(self):
        self.setWindowTitle("Serial Reader")
        self.setFixedSize(1280, 900)

        self.label = QLabel("Waiting for data...")
        self.measure_button = QPushButton("Measure Component")
        self.port_button = QPushButton("Select COM Port")
        self.wifi_button = QPushButton("Set WiFi Credentials")

        self.measure_button.setFixedWidth(200)
        self.port_button.setFixedWidth(200)
        self.wifi_button.setFixedWidth(200)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.measure_button)
        layout.addWidget(self.port_button)
        layout.addWidget(self.wifi_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.measure_button.clicked.connect(lambda: self.send_data("Measure object"))
        self.port_button.clicked.connect(self.select_port)
        self.wifi_button.clicked.connect(self.set_wifi_credentials)

    def serial_init(self):
        self.serial_thread = SerialThread()
        self.serial_thread.signal.connect(self.update_label)
        self.serial_thread.start()

    def update_label(self, data):
        self.label.setText(data)

    def send_data(self, data):
        self.serial_thread.send_data(data)

    def select_port(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        port, ok = QInputDialog.getItem(self, "Select COM Port", "COM Port:", ports, 0, False)
        if ok and port:
            self.serial_thread.set_serial_port(port)

    def set_wifi_credentials(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Set WiFi Credentials")
        layout = QFormLayout(dialog)

        ssid_edit = QLineEdit(dialog)
        layout.addRow("WiFi SSID:", ssid_edit)

        password_edit = QLineEdit(dialog)
        password_edit.setEchoMode(QLineEdit.Password)
        layout.addRow("WiFi Password (leave blank if not password):", password_edit)

        ok_button = QPushButton("OK", dialog)
        ok_button.clicked.connect(dialog.accept)
        layout.addRow(ok_button)

        if dialog.exec_() == QDialog.Accepted:
            ssid = ssid_edit.text()
            password = password_edit.text()
            self.send_data(f"SSID:{ssid},PASSWORD:{password}")

            credentials = base64.b64encode(ssid.encode()).decode() + "::" + base64.b64encode(password.encode()).decode()
            with open(self.credentials_file, "w") as f:
                f.write(credentials)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
