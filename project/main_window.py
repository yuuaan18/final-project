# main_window.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QStackedWidget, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap
from dashboard_panel import DashboardPanel
from products_panel import ProductsPanel
from transactions_panel import TransactionsPanel
from admins_panel import AdminsPanel


class MainWindow(QWidget):
    def __init__(self, user_id, username, role):
        super().__init__()
        self.setWindowTitle("TechStore POS")
        self.showMaximized()

        self.user_id = user_id
        self.username = username
        self.role = role
        self.active_button = None  # ✅ track active button

        # ===== Main layout =====
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ===== Sidebar =====
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(15)

        # ===== Logo & Title =====
        logo = QLabel()
        pixmap = QPixmap("assets/logo.png")

        if not pixmap.isNull():
            pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pixmap)
        else:
            # fallback text if image not found
            logo.setText("LOGO")
            logo.setStyleSheet("font-size: 14px; color: gray;")

        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        app_name = QLabel("TechStore POS")
        app_name.setObjectName("appName")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(f"{role.capitalize()}'s Portal")
        subtitle.setObjectName("appSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sidebar_layout.addWidget(logo)
        sidebar_layout.addWidget(app_name)
        sidebar_layout.addWidget(subtitle)

        # Separator line
        top_line = QFrame()
        top_line.setFrameShape(QFrame.Shape.HLine)
        top_line.setFrameShadow(QFrame.Shadow.Sunken)
        sidebar_layout.addWidget(top_line)

        # ===== Sidebar Buttons =====
        self.dashboard_btn = QPushButton(" Dashboard")
        self.products_btn = QPushButton(" Products")
        self.transactions_btn = QPushButton(" Transactions")
        self.admins_btn = QPushButton(" Admin Tools")

        self.nav_buttons = [self.dashboard_btn, self.products_btn,
                            self.transactions_btn, self.admins_btn]

        for btn in self.nav_buttons:
            btn.setObjectName("navButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setIconSize(QSize(20, 20))
            btn.clicked.connect(lambda checked, b=btn: self.set_active_button(b))

        # ===== Role-based button display =====
        if role == "admin":
            # Admin sees: Dashboard, Products, Transactions, Admin Tools
            sidebar_layout.addWidget(self.dashboard_btn)
            sidebar_layout.addWidget(self.products_btn)
            sidebar_layout.addWidget(self.transactions_btn)
            sidebar_layout.addWidget(self.admins_btn)
        else:
            # Cashier sees: Transactions only
            sidebar_layout.addWidget(self.transactions_btn)

        sidebar_layout.addStretch()

        # Separator before logout
        bottom_line = QFrame()
        bottom_line.setFrameShape(QFrame.Shape.HLine)
        bottom_line.setFrameShadow(QFrame.Shadow.Sunken)
        sidebar_layout.addWidget(bottom_line)

        # ===== Logout Button at Bottom =====
        self.logout_btn = QPushButton(" Logout")
        self.logout_btn.setObjectName("logoutButton")
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sidebar_layout.addWidget(self.logout_btn)

        # ===== Content Area =====
        self.stack = QStackedWidget()

        # Panels
        self.dashboard_panel = DashboardPanel(username, role)
        self.products_panel = ProductsPanel()
        self.transactions_panel = TransactionsPanel(self.user_id)
        self.admins_panel = AdminsPanel()

        # Add panels to stack
        self.stack.addWidget(self.dashboard_panel)
        self.stack.addWidget(self.products_panel)
        self.stack.addWidget(self.transactions_panel)
        self.stack.addWidget(self.admins_panel)

        # Add to layout
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stack)

        # Connect buttons to panels
        self.dashboard_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.dashboard_panel))
        self.products_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.products_panel))
        self.transactions_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.transactions_panel))
        self.admins_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.admins_panel))
        self.logout_btn.clicked.connect(self.handle_logout)

        # ✅ Set default active button and panel based on role
        if role == "admin":
            self.set_active_button(self.dashboard_btn)
            self.stack.setCurrentWidget(self.dashboard_panel)
        else:
            # Cashier starts with transactions panel
            self.set_active_button(self.transactions_btn)
            self.stack.setCurrentWidget(self.transactions_panel)

        # Apply styles safely
        try:
            with open("qss/sidebar.qss", "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"⚠️ Could not load sidebar.qss: {e}")

    def set_active_button(self, button):
        """Highlight the selected nav button"""
        if self.active_button:
            self.active_button.setProperty("active", False)
            self.active_button.style().unpolish(self.active_button)
            self.active_button.style().polish(self.active_button)

        button.setProperty("active", True)
        button.style().unpolish(button)
        button.style().polish(button)

        self.active_button = button

    def handle_logout(self):
        """Show confirmation dialog before logging out"""
        confirm = QMessageBox.question(
            self,
            "Confirm Logout",
            f"Are you sure you want to logout, {self.username}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Default to No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            from login_window import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.showMaximized()
            self.close()