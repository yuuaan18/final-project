# products_panel.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QFrame,
    QMessageBox, QDialog, QFormLayout, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer
import pymysql


class ProductDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.setWindowTitle("Product Form")
        self.setFixedWidth(420)

        self.setStyleSheet("""
            QDialog {
                background: #fff;
                border-radius: 12px;
                padding: 20px;
            }
            QLabel { font-size: 14px; }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 6px;
                font-size: 13px;
                color: black;
                background: white;
            }
            QComboBox QAbstractItemView {
                background: white;
                color: black;
                selection-background-color: #007BFF;
                selection-color: white;
            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        self.name_input = QLineEdit()
        self.category_input = QComboBox()
        self.category_input.addItems([
            "Processor", "GPU", "Motherboard", "Memory",
            "Storage", "Keyboard", "Mouse", "Monitor",
            "PSU", "Case", "Accessories"
        ])
        self.price_input = QLineEdit()
        self.stock_input = QLineEdit()

        form.addRow("Product Name:", self.name_input)
        form.addRow("Category:", self.category_input)
        form.addRow("Price (₱):", self.price_input)
        form.addRow("Stock:", self.stock_input)

        layout.addLayout(form)

        btns = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        btns.addWidget(self.save_btn)
        btns.addWidget(self.cancel_btn)
        layout.addLayout(btns)

        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self.accept)

        if product:
            self.name_input.setText(product["name"])
            self.category_input.setCurrentText(product["category"])
            self.price_input.setText(str(product["price"]))
            self.stock_input.setText(str(product["stock"]))

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "category": self.category_input.currentText(),
            "price": float(self.price_input.text().strip()),
            "stock": int(self.stock_input.text().strip())
        }


class ProductsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Products")
        self.selected_row = None

        # Store references to stat card labels
        self.stat_labels = {}

        layout = QVBoxLayout(self)

        # === Header (matching dashboard) ===
        header_layout = QVBoxLayout()
        title = QLabel("Products")
        subtitle = QLabel("Manage computer parts catalog and sales")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-top: 15px;")
        subtitle.setStyleSheet("font-size: 13px; color: gray; margin-bottom: 10px;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        # === Stats Row (separate cards like dashboard) ===
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(12)

        self.create_stat_cards()

        # === Controls Card ===
        controls_card = QFrame()
        controls_card.setStyleSheet("""
            QFrame {
                background: #fff;
                border-radius: 12px;
                padding: 12px;
                border: 1px solid #eee;
            }
        """)
        controls_layout = QHBoxLayout(controls_card)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by ID, name, or category...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border-radius: 8px;
                border: 1px solid #ddd;
                font-size: 13px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #007BFF;
            }
        """)

        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.addItems([
            "Processor", "GPU", "Motherboard", "Memory",
            "Storage", "Keyboard", "Mouse", "Monitor",
            "PSU", "Case", "Accessories"
        ])
        self.category_filter.setStyleSheet("""
            QComboBox {
                padding: 10px;
                font-size: 13px;
                color: #333;
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
            QComboBox:hover {
                border: 1px solid #007BFF;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background: white;
                color: #333;
                selection-background-color: #007BFF;
                selection-color: white;
                border: 1px solid #ddd;
                padding: 5px;
            }
        """)

        self.add_btn = QPushButton("+ Add Product")
        self.edit_btn = QPushButton("✏ Edit")
        self.delete_btn = QPushButton("🗑 Delete")

        for btn in (self.add_btn, self.edit_btn, self.delete_btn):
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #007BFF;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 18px;
                    font-weight: 600;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
                QPushButton:pressed {
                    background-color: #004085;
                }
            """)

        controls_layout.addWidget(self.search_input, stretch=2)
        controls_layout.addWidget(self.category_filter, stretch=1)
        controls_layout.addWidget(self.add_btn)
        controls_layout.addWidget(self.edit_btn)
        controls_layout.addWidget(self.delete_btn)

        # === Products Table Label ===
        table_label = QLabel("Product Inventory")
        table_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 15px; margin-bottom: 8px;")

        # === Table (matching dashboard) ===
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Product Name", "Category", "Price (₱)", "Stock"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QHeaderView::section {
                background-color: #f5f5f5;
                color: black;
                font-weight: bold;
                font-size: 13px;
                padding: 6px;
                border: 1px solid #dcdcdc;
            }
            QTableWidget {
                gridline-color: #dcdcdc;
                font-size: 13px;
                color: black;
                alternate-background-color: #fafafa;
                border: 1px solid #dcdcdc;
            }
            QTableWidget::item {
                padding: 8px;
            }
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellClicked.connect(self.on_row_click)

        # === Add everything ===
        layout.addLayout(header_layout)
        layout.addLayout(self.stats_row)
        layout.addWidget(controls_card)
        layout.addWidget(table_label)
        layout.addWidget(self.table)

        self.load_products()

        # Connect buttons
        self.add_btn.clicked.connect(self.add_product)
        self.edit_btn.clicked.connect(self.edit_product)
        self.delete_btn.clicked.connect(self.delete_product)
        self.search_input.textChanged.connect(self.search_products)
        self.category_filter.currentTextChanged.connect(self.search_products)

        # Set up auto-refresh timer (refreshes every 5 seconds)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_stats)
        self.refresh_timer.start(5000)  # 5000 ms = 5 seconds

    def create_stat_cards(self):
        """Create stat cards and store label references"""
        # Clear existing cards
        for i in reversed(range(self.stats_row.count())):
            widget = self.stats_row.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Get product stats
        conn = self.db_connect()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM products")
        total_products = cursor.fetchone()["total"]

        cursor.execute("SELECT SUM(stock) as total FROM products")
        total_stock = cursor.fetchone()["total"] or 0

        cursor.execute("SELECT COUNT(*) as low FROM products WHERE stock < 10")
        low_stock = cursor.fetchone()["low"]

        cursor.execute("SELECT COUNT(DISTINCT category) as cats FROM products")
        total_categories = cursor.fetchone()["cats"]

        cursor.close()
        conn.close()

        # Create cards
        stats = [
            ("Total Products", str(total_products), "total_products"),
            ("Total Stock", str(total_stock), "total_stock"),
            ("Low Stock Items", str(low_stock), "low_stock"),
            ("Categories", str(total_categories), "categories")
        ]

        for title, value, key in stats:
            card, label = self.create_stat_card(title, value)
            self.stat_labels[key] = label
            self.stats_row.addWidget(card)

    def create_stat_card(self, title, value):
        """Create individual stat cards like dashboard"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #fff;
                border-radius: 12px;
                padding: 16px;
                border: 1px solid #eee;
            }
        """)
        # === ADJUST CARD SIZE HERE ===
        # Change this value to make cards taller or shorter (in pixels)
        card.setFixedHeight(140)  # Reduced from 110 to 85 for better fit
        # =============================

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            "font-size: 13px; color: #666; font-weight: normal; border: none; background: transparent;")
        layout.addWidget(lbl_title, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        layout.addStretch()

        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #007BFF; border: none; background: transparent;")
        layout.addWidget(lbl_value, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        return card, lbl_value

    def refresh_stats(self):
        """Refresh stat card values without rebuilding UI"""
        conn = self.db_connect()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM products")
        total_products = cursor.fetchone()["total"]

        cursor.execute("SELECT SUM(stock) as total FROM products")
        total_stock = cursor.fetchone()["total"] or 0

        cursor.execute("SELECT COUNT(*) as low FROM products WHERE stock < 10")
        low_stock = cursor.fetchone()["low"]

        cursor.execute("SELECT COUNT(DISTINCT category) as cats FROM products")
        total_categories = cursor.fetchone()["cats"]

        cursor.close()
        conn.close()

        # Update labels
        if "total_products" in self.stat_labels:
            self.stat_labels["total_products"].setText(str(total_products))
        if "total_stock" in self.stat_labels:
            self.stat_labels["total_stock"].setText(str(total_stock))
        if "low_stock" in self.stat_labels:
            self.stat_labels["low_stock"].setText(str(low_stock))
        if "categories" in self.stat_labels:
            self.stat_labels["categories"].setText(str(total_categories))

    def db_connect(self):
        return pymysql.connect(
            host="localhost",
            user="root",
            password="",
            database="techstore_pos",
            cursorclass=pymysql.cursors.DictCursor
        )

    def load_products(self, query="SELECT * FROM products", params=None):
        conn = self.db_connect()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 35)
            self.table.setItem(r, 0, QTableWidgetItem(str(row["id"]).zfill(10)))
            self.table.setItem(r, 1, QTableWidgetItem(row["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(row["category"]))
            self.table.setItem(r, 3, QTableWidgetItem(f"₱{row['price']:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(str(row["stock"])))

    def on_row_click(self, row, col):
        self.selected_row = row

    def add_product(self):
        dialog = ProductDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            conn = self.db_connect()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (name, category, price, stock)
                VALUES (%s, %s, %s, %s)
            """, (data["name"], data["category"], data["price"], data["stock"]))
            conn.commit()
            cursor.close()
            conn.close()

            # Show success message
            QMessageBox.information(
                self,
                "Success",
                f"Product '{data['name']}' added successfully!"
            )

            self.load_products()
            self.refresh_stats()  # Immediately refresh stats after adding

    def edit_product(self):
        if self.selected_row is None:
            QMessageBox.warning(self, "No Selection", "Please select a product to edit.")
            return

        pid = int(self.table.item(self.selected_row, 0).text())
        product = {
            "name": self.table.item(self.selected_row, 1).text(),
            "category": self.table.item(self.selected_row, 2).text(),
            "price": float(self.table.item(self.selected_row, 3).text().replace("₱", "")),
            "stock": int(self.table.item(self.selected_row, 4).text())
        }

        dialog = ProductDialog(self, product)
        if dialog.exec():
            data = dialog.get_data()
            conn = self.db_connect()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE products SET name=%s, category=%s, price=%s, stock=%s WHERE id=%s
            """, (data["name"], data["category"], data["price"], data["stock"], pid))
            conn.commit()
            cursor.close()
            conn.close()

            # Show success message
            QMessageBox.information(
                self,
                "Success",
                f"Product '{data['name']}' updated successfully!"
            )

            self.load_products()
            self.refresh_stats()  # Immediately refresh stats after editing

    def delete_product(self):
        if self.selected_row is None:
            QMessageBox.warning(self, "No Selection", "Please select a product to delete.")
            return

        pid = int(self.table.item(self.selected_row, 0).text())
        product_name = self.table.item(self.selected_row, 1).text()

        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{product_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            conn = self.db_connect()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id=%s", (pid,))
            conn.commit()
            cursor.close()
            conn.close()

            # Show success message
            QMessageBox.information(
                self,
                "Success",
                f"Product '{product_name}' deleted successfully!"
            )

            self.load_products()
            self.refresh_stats()  # Immediately refresh stats after deleting

    def search_products(self):
        text = self.search_input.text().strip()
        category = self.category_filter.currentText()

        query = "SELECT * FROM products WHERE 1=1"
        params = []

        if text:
            query += " AND (id LIKE %s OR name LIKE %s OR category LIKE %s)"
            like = f"%{text}%"
            params.extend([like, like, like])

        if category != "All Categories":
            query += " AND category=%s"
            params.append(category)

        self.load_products(query, params)

    def closeEvent(self, event):
        """Stop timer when widget is closed"""
        self.refresh_timer.stop()
        event.accept()