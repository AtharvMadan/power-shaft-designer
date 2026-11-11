import os
import subprocess
import sys

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QPushButton, QMessageBox)
from PyQt5.QtCore import Qt

HERE = os.path.dirname(os.path.abspath(__file__))


class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shaft Designer Launcher")
        self.setFixedWidth(360)
        self.designer = None

        layout = QVBoxLayout(self)
        title = QLabel("<h2>Power Transmission Shaft Designer</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(QLabel("ASME elliptic fatigue design with a torsional rigidity check."))

        btn_open = QPushButton("Open Shaft Designer")
        btn_open.setStyleSheet(
            "background-color: #1565c0; color: white; font-weight: bold; padding: 10px;")
        btn_open.clicked.connect(self.open_designer)
        layout.addWidget(btn_open)

        btn_check = QPushButton("Run Self-Check")
        btn_check.clicked.connect(self.run_self_check)
        layout.addWidget(btn_check)

        btn_exit = QPushButton("Exit")
        btn_exit.clicked.connect(self.close)
        layout.addWidget(btn_exit)

    def open_designer(self):
        try:
            from main_ui import MainWindow
            self.designer = MainWindow()
            self.designer.show()
            self.hide()
            self.designer.destroyed.connect(self.show)
        except Exception as e:
            QMessageBox.critical(self, "Could not open the designer", str(e))

    def run_self_check(self):
        script = os.path.join(HERE, "test_handcheck.py")
        if not os.path.exists(script):
            QMessageBox.warning(self, "Self-check", "test_handcheck.py was not found.")
            return
        result = subprocess.run([sys.executable, script], cwd=HERE,
                                capture_output=True, text=True)
        text = (result.stdout + result.stderr).strip()
        if result.returncode == 0:
            QMessageBox.information(self, "Self-check passed", text)
        else:
            QMessageBox.critical(self, "Self-check failed", text)


def main():
    app = QApplication(sys.argv)
    window = Launcher()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
