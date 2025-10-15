from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QMessageBox, QScrollArea, QFrame, QGridLayout,
    QComboBox, QSpacerItem, QSizePolicy, QDialog, QTextEdit
)
from PyQt6.QtCore import Qt
from functools import partial
from db import safe_query
import datetime
import json


class ReceiptDialog(QDialog):
    def __init__(self, parent=None, receipt_data=None):
        super().__init__(parent)
        self.setWindowTitle("Transaction Receipt")
        self.setFixedWidth(450)
        self.setStyleSheet("""
            QDialog {
                background: #fff;
            }
        """)

        layout = QVBoxLayout(self)

        # Receipt text area
        receipt_text = QTextEdit()
        receipt_text.setReadOnly(True)
        receipt_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #ddd;
                padding: 15px;
                background: white;
                color: black;
            }
        """)

        # Build receipt content
        receipt_content = self.build_receipt(receipt_data)
        receipt_text.setPlainText(receipt_content)

        layout.addWidget(receipt_text)

        # Button
        btn_layout = QHBoxLayout()

        ok_btn = QPushButton("Complete Transaction")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        ok_btn.clicked.connect(self.accept)

        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.receipt_text = receipt_text

    def build_receipt(self, data):
        """Build formatted receipt text"""
        receipt = []
        receipt.append("=" * 48)
        receipt.append("          TECHSTORE POS RECEIPT")
        receipt.append("=" * 48)
        receipt.append("")
        receipt.append(f"Date: {data['date']}")
        receipt.append(f"Time: {data['time']}")
        receipt.append(f"Transaction ID: {data['transaction_id']}")
        receipt.append(f"Cashier: {data['cashier']}")
        receipt.append("")
        receipt.append("-" * 48)
        receipt.append(f"{'ITEM':<25} {'QTY':<6} {'PRICE':>10}")
        receipt.append("-" * 48)

        for item in data['items']:
            name = item['name'][:25]  # Truncate long names
            receipt.append(f"{name:<25} {item['qty']:<6} ₱{item['price']:>9.2f}")
            total_price = item['qty'] * item['price']
            receipt.append(f"{'':>33} ₱{total_price:>9.2f}")

        receipt.append("-" * 48)
        receipt.append(f"{'Subtotal:':<35} ₱{data['subtotal']:>9.2f}")
        receipt.append(f"{'Tax (12%):':<35} ₱{data['tax']:>9.2f}")
        receipt.append("=" * 48)
        receipt.append(f"{'TOTAL:':<35} ₱{data['total']:>9.2f}")
        receipt.append(f"{'Payment:':<35} ₱{data['payment']:>9.2f}")
        receipt.append(f"{'Change:':<35} ₱{data['change']:>9.2f}")
        receipt.append("=" * 48)
        receipt.append("")
        receipt.append("     Thank you for shopping with us!")
        receipt.append("          Please come again!")
        receipt.append("=" * 48)

        return "\n".join(receipt)


class TransactionsPanel(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.setWindowTitle("Transactions")

        self.user_id = user_id
        self.cart = []  # list of {id, name, price, qty}

        # ===== Main Layout =====
        main_layout = QVBoxLayout(self)

        # ===== Header =====
        header_layout = QVBoxLayout()
        title = QLabel("Transactions")
        subtitle = QLabel("Process customer purchases and manage sales")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-top: 15px;")
        subtitle.setStyleSheet("font-size: 13px; color: gray; margin-bottom: 10px;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)

        # ===== Search + Filter =====
        filter_card = QFrame()
        filter_card.setStyleSheet("""
            QFrame {
                background: #fff;
                border-radius: 12px;
                padding: 12px;
                border: 1px solid #eee;
            }
        """)
        filter_layout = QHBoxLayout(filter_card)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by product name or ID...")
        self.search_input.textChanged.connect(self.search_products)
        self.search_input.setStyleSheet("padding: 8px; border-radius: 8px; border: 1px solid #ccc; font-size: 13px;")

        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        categories = safe_query("SELECT DISTINCT category FROM products", fetch="all")
        if categories:
            for c in categories:
                self.category_filter.addItem(c["category"])
        self.category_filter.currentTextChanged.connect(self.search_products)
        self.category_filter.setStyleSheet("""
            QComboBox {
                padding: 6px;
                font-size: 13px;
                color: black;
                background: white;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
            QComboBox QAbstractItemView {
                background: white;
                color: black;
            }
        """)

        filter_layout.addWidget(self.search_input, stretch=2)
        filter_layout.addWidget(self.category_filter, stretch=1)

        main_layout.addWidget(filter_card)

        # ===== Content Split =====
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout, stretch=1)

        # ===== Left Side: Products =====
        left_layout = QVBoxLayout()

        self.products_area = QScrollArea()
        self.products_area.setWidgetResizable(True)
        self.products_frame = QFrame()
        self.products_layout = QGridLayout(self.products_frame)
        self.products_layout.setSpacing(10)
        self.products_area.setWidget(self.products_frame)
        left_layout.addWidget(self.products_area)

        content_layout.addLayout(left_layout, 2)

        # ===== Right Side: Cart =====
        right_layout = QVBoxLayout()

        cart_title = QLabel("🛒 Cart")
        cart_title.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            margin-bottom: 5px; 
            border-bottom: 2px solid #ccc;
        """)
        right_layout.addWidget(cart_title)

        # Cart Table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(3)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Price", "Actions"])
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cart_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.cart_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        self.cart_table.horizontalHeader().setSectionResizeMode(0,
                                                                self.cart_table.horizontalHeader().ResizeMode.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(1,
                                                                self.cart_table.horizontalHeader().ResizeMode.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(2,
                                                                self.cart_table.horizontalHeader().ResizeMode.ResizeToContents)

        self.cart_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                font-size: 13px;
                color: black;
                gridline-color: #ccc;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: black;
                font-weight: bold;
                font-size: 13px;
                padding: 6px;
                border: 1px solid #ddd;
                height: 35px;
            }
        """)
        self.cart_table.verticalHeader().setDefaultSectionSize(50)
        right_layout.addWidget(self.cart_table)

        # Order Summary
        self.subtotal_label = QLabel("Subtotal: ₱0.00")
        self.tax_label = QLabel("Tax (12%): ₱0.00")
        self.total_label = QLabel("Total: ₱0.00")
        for lbl in (self.subtotal_label, self.tax_label, self.total_label):
            lbl.setStyleSheet("font-size: 13px; color: black; margin-top: 4px;")
            right_layout.addWidget(lbl)

        self.payment_input = QLineEdit()
        self.payment_input.setPlaceholderText("Enter cash payment")
        self.payment_input.setStyleSheet("padding: 8px; border-radius: 8px; border: 1px solid #ccc;")
        self.payment_input.textChanged.connect(self.validate_payment)
        right_layout.addWidget(self.payment_input)

        self.complete_btn = QPushButton("Complete Transaction")
        self.complete_btn.setEnabled(False)
        self.complete_btn.setStyleSheet("""
            QPushButton {
                background-color: #cccccc;
                color: #666666;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
        """)
        self.complete_btn.clicked.connect(self.complete_transaction)
        right_layout.addWidget(self.complete_btn)

        content_layout.addLayout(right_layout, 1)

        self.load_products()

    # ===== Load Products =====
    def load_products(self, category=None, search_text=None):
        query = "SELECT * FROM products WHERE stock > 0"
        params = []

        if category and category != "All Categories":
            query += " AND category=%s"
            params.append(category)

        if search_text:
            query += " AND (name LIKE %s OR id LIKE %s)"
            like = f"%{search_text}%"
            params.extend([like, like])

        products = safe_query(query, tuple(params), fetch="all") or []

        for i in reversed(range(self.products_layout.count())):
            item = self.products_layout.itemAt(i).widget()
            if item:
                item.setParent(None)

        # Always 3 columns per row
        for idx, p in enumerate(products):
            card = QFrame()
            card.setObjectName("productCard")

            # === ADJUST PRODUCT CARD HEIGHT HERE ===
            # Change this value to adjust card height (in pixels)
            card.setFixedHeight(160)  # Height: 160px
            # Width will stretch to fit panel nicely
            # =======================================

            card.setStyleSheet("""
                QFrame#productCard {
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    padding: 10px;
                    background: white;
                }
                QFrame#productCard:hover {
                    border: 1px solid #007BFF;
                    background: #f8f9fa;
                }
            """)
            vbox = QVBoxLayout(card)
            vbox.setSpacing(6)
            vbox.setContentsMargins(8, 8, 8, 8)

            name = QLabel(p["name"])
            name.setObjectName("productName")
            name.setWordWrap(True)
            name.setMaximumHeight(40)
            name.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")

            category_label = QLabel(p["category"])
            category_label.setStyleSheet("font-size: 11px; color: #666;")

            price = QLabel(f"₱{p['price']:.2f}")
            price.setObjectName("productPrice")
            price.setStyleSheet("font-size: 14px; font-weight: bold; color: #007BFF;")

            add_btn = QPushButton("Add to Cart")
            add_btn.setFixedHeight(30)
            add_btn.setStyleSheet("""
                QPushButton {
                    background-color: #007BFF;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
            add_btn.clicked.connect(partial(self.add_to_cart, p))

            vbox.addWidget(name)
            vbox.addWidget(category_label)
            vbox.addStretch()
            vbox.addWidget(price)
            vbox.addWidget(add_btn)

            row, col = divmod(idx, 3)
            self.products_layout.addWidget(card, row, col)

        # Make columns stretch equally to fill space
        for col in range(3):
            self.products_layout.setColumnStretch(col, 1)

        # Add stretch to bottom to prevent cards from stretching vertically
        self.products_layout.setRowStretch(self.products_layout.rowCount(), 1)

    def search_products(self):
        text = self.search_input.text().strip()
        category = self.category_filter.currentText()
        self.load_products(category, text)

    # ===== Add Product to Cart =====
    def add_to_cart(self, product):
        pid = product.get("id")
        name = product.get("name", "Unknown")
        price = float(product.get("price", 0))

        for item in self.cart:
            if item["id"] == pid:
                item["qty"] += 1
                break
        else:
            self.cart.append({"id": pid, "name": name, "price": price, "qty": 1})

        self.refresh_cart()

    # ===== Refresh Cart Table =====
    def refresh_cart(self):
        self.cart_table.setRowCount(0)
        for item in self.cart:
            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)

            self.cart_table.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.cart_table.setItem(row, 1, QTableWidgetItem(f"₱{item['price']:.2f}"))

            # Actions: [-] qty [+]
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 5, 5, 5)
            action_layout.setSpacing(5)

            minus_btn = QPushButton("-")
            minus_btn.setFixedSize(30, 30)
            minus_btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    font-weight: bold;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    background-color: #007BFF;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
            minus_btn.clicked.connect(partial(self.update_quantity, item["id"], -1))

            qty_input = QLineEdit(str(item["qty"]))
            qty_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qty_input.setFixedWidth(45)
            qty_input.setFixedHeight(30)
            qty_input.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    padding: 2px;
                    font-size: 13px;
                }
            """)
            qty_input.textChanged.connect(partial(self.validate_quantity_input, qty_input, item["id"]))
            qty_input.editingFinished.connect(partial(self.update_quantity_from_input, qty_input, item["id"]))

            plus_btn = QPushButton("+")
            plus_btn.setFixedSize(30, 30)
            plus_btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    font-weight: bold;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    background-color: #007BFF;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
            plus_btn.clicked.connect(partial(self.update_quantity, item["id"], 1))

            action_layout.addWidget(minus_btn)
            action_layout.addWidget(qty_input)
            action_layout.addWidget(plus_btn)

            self.cart_table.setCellWidget(row, 2, action_widget)

        self.update_totals()

    def update_quantity(self, pid, delta):
        for item in self.cart:
            if item["id"] == pid:
                item["qty"] += delta
                if item["qty"] <= 0:
                    self.cart.remove(item)
                break
        self.refresh_cart()

    def validate_quantity_input(self, qty_input, pid):
        """Validate quantity input to only allow digits"""
        text = qty_input.text()
        # Remove any non-digit characters
        valid_text = ''.join(c for c in text if c.isdigit())
        if text != valid_text:
            qty_input.setText(valid_text)

    def update_quantity_from_input(self, qty_input, pid):
        """Update cart quantity when user edits the input field"""
        text = qty_input.text().strip()

        if not text or text == "0":
            # If empty or zero, remove item from cart
            for item in self.cart:
                if item["id"] == pid:
                    self.cart.remove(item)
                    break
            self.refresh_cart()
            return

        try:
            new_qty = int(text)
            if new_qty > 0:
                for item in self.cart:
                    if item["id"] == pid:
                        item["qty"] = new_qty
                        break
                self.refresh_cart()
        except ValueError:
            # If invalid, just refresh to restore original value
            self.refresh_cart()

    def update_totals(self):
        subtotal = sum(item["price"] * item["qty"] for item in self.cart)
        tax = subtotal * 0.12
        total = subtotal + tax
        self.subtotal_label.setText(f"Subtotal: ₱{subtotal:.2f}")
        self.tax_label.setText(f"Tax (12%): ₱{tax:.2f}")
        self.total_label.setText(f"Total: ₱{total:.2f}")
        self.validate_payment()

    def validate_payment(self):
        """Validate payment input and enable/disable complete button"""
        payment_text = self.payment_input.text().strip()

        # Check if input contains only digits (and optionally a decimal point)
        if payment_text:
            # Allow only digits and one decimal point
            if not all(c.isdigit() or c == '.' for c in payment_text):
                # Remove invalid characters
                valid_text = ''.join(c for c in payment_text if c.isdigit() or c == '.')
                self.payment_input.setText(valid_text)
                return

            # Check for multiple decimal points
            if payment_text.count('.') > 1:
                # Keep only first decimal point
                parts = payment_text.split('.')
                valid_text = parts[0] + '.' + ''.join(parts[1:])
                self.payment_input.setText(valid_text)
                return

        # Calculate total
        subtotal = sum(item["price"] * item["qty"] for item in self.cart)
        tax = subtotal * 0.12
        total = subtotal + tax

        # Check if payment is valid and sufficient
        try:
            payment = float(payment_text) if payment_text else 0
            if payment >= total and total > 0:
                self.complete_btn.setEnabled(True)
                self.complete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #007BFF;
                        color: white;
                        border-radius: 6px;
                        padding: 10px;
                        font-weight: bold;
                    }
                    QPushButton:hover { background-color: #0056b3; }
                """)
            else:
                self.complete_btn.setEnabled(False)
                self.complete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #cccccc;
                        color: #666666;
                        border-radius: 6px;
                        padding: 10px;
                        font-weight: bold;
                    }
                """)
        except ValueError:
            self.complete_btn.setEnabled(False)
            self.complete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #cccccc;
                    color: #666666;
                    border-radius: 6px;
                    padding: 10px;
                    font-weight: bold;
                }
            """)

    def complete_transaction(self):
        if not self.cart:
            QMessageBox.warning(self, "Error", "Cart is empty!")
            return

        try:
            payment = float(self.payment_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid payment amount.")
            return

        subtotal = sum(item["price"] * item["qty"] for item in self.cart)
        tax = subtotal * 0.12
        total = subtotal + tax

        if payment < total:
            QMessageBox.warning(self, "Error", "Payment is less than total.")
            return

        change = payment - total

        # Show change confirmation
        confirm = QMessageBox.information(
            self,
            "Payment Received",
            f"Payment: ₱{payment:.2f}\nTotal: ₱{total:.2f}\n\nChange: ₱{change:.2f}",
            QMessageBox.StandardButton.Ok
        )

        # Get cashier name
        cashier_data = safe_query("SELECT username FROM users WHERE id = %s", (self.user_id,))
        cashier_name = cashier_data["username"] if cashier_data else "Unknown"

        # Prepare receipt data
        now = datetime.datetime.now()
        receipt_data = {
            'date': now.strftime("%Y-%m-%d"),
            'time': now.strftime("%H:%M:%S"),
            'transaction_id': '',  # Will be set after insert
            'cashier': cashier_name,
            'items': self.cart.copy(),
            'subtotal': subtotal,
            'tax': tax,
            'total': total,
            'payment': payment,
            'change': change
        }

        # Process transaction - Insert into transactions table
        safe_query("INSERT INTO transactions (user_id, total) VALUES (%s, %s)", (self.user_id, total), fetch=None)
        transaction_id = safe_query("SELECT LAST_INSERT_ID() as id")["id"]

        receipt_data['transaction_id'] = str(transaction_id).zfill(10)

        # Insert transaction items
        for item in self.cart:
            safe_query(
                "INSERT INTO transaction_items (transaction_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
                (transaction_id, item["id"], item["qty"], item["price"]), fetch=None
            )
            safe_query("UPDATE products SET stock = stock - %s WHERE id = %s", (item["qty"], item["id"]), fetch=None)

        # Save receipt to database
        receipt_json = json.dumps(receipt_data)
        safe_query(
            "INSERT INTO receipts (transaction_id, receipt_data, created_at) VALUES (%s, %s, %s)",
            (transaction_id, receipt_json, now), fetch=None
        )

        # Show receipt dialog
        receipt_dialog = ReceiptDialog(self, receipt_data)
        receipt_dialog.exec()

        # Clear cart
        self.cart.clear()
        self.refresh_cart()
        self.payment_input.clear()
        self.load_products()