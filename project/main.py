import sys
from PyQt6.QtWidgets import QApplication
from login_window import LoginWindow

def load_stylesheet(filename):
    """Load external QSS file"""
    with open(filename, "r") as f:
        return f.read()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Example: start login window
    app.setStyleSheet(load_stylesheet("qss/login.qss"))
    window = LoginWindow()

    window.show()
    sys.exit(app.exec())
