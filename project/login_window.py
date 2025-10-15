# login_window.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QHBoxLayout, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt

from db import safe_query
from main_window import MainWindow


def load_stylesheet(filename):
    """Helper to load QSS file from qss directory"""
    try:
        with open(f"qss/{filename}", "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"⚠️ Stylesheet {filename} not found in qss folder.")
        return ""


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TechStore POS - Login")

        # ✅ Fullscreen mode
        self.showMaximized()

        # ✅ Apply login stylesheet
        self.setStyleSheet(load_stylesheet("login.qss"))

        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(400)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 50))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout()
        card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("TechStore POS")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Computer Parts System")
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Enter your username")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Enter your password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        # ✅ Sign In button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setFixedHeight(40)
        self.login_btn.clicked.connect(self.handle_login)

        # ✅ Make it default (Enter ↵ anywhere will trigger it)
        self.login_btn.setDefault(True)
        self.login_btn.setAutoDefault(True)

        # ✅ Error label instead of QMessageBox
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: red;")

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(20)
        card_layout.addWidget(self.username)
        card_layout.addWidget(self.password)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.login_btn)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.error_label)

        card.setLayout(card_layout)
        main_layout.addWidget(card)
        self.setLayout(main_layout)

    def handle_login(self):
        user = self.username.text().strip()
        pwd = self.password.text().strip()

        query = "SELECT * FROM users WHERE username=%s AND password=%s"
        account = safe_query(query, (user, pwd))

        if account:
            role = account["role"]
            user_id = account["id"]

            # ✅ Go straight to main window
            self.main_window = MainWindow(user_id, user, role)
            self.main_window.show()
            self.close()
        else:
            self.error_label.setText("Invalid username or password.")