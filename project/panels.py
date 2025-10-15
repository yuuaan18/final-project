# panels.py
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout


class ProductsPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Products Panel (to be implemented)"))


class TransactionsPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Transactions Panel (to be implemented)"))


class CustomersPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Customers Panel (to be implemented)"))


class AdminsPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Admins Panel (to be implemented)"))


class EarningsPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Earnings Panel (to be implemented)"))
