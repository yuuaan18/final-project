# earnings_panel.py
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from db import safe_query


class EarningsPanel(QWidget):
    def __init__(self):
        super().__init__()

        # Store references to card value labels
        self.card_labels = {}

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(25)

        # ===== Header =====
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)

        title = QLabel("Earnings Overview")
        subtitle = QLabel("Track your daily, weekly, and monthly revenue performance")

        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1a1a1a;")
        subtitle.setStyleSheet("font-size: 14px; color: #666;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        self.main_layout.addLayout(header_layout)

        # ===== Cards Layout =====
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(16)

        self.create_cards()
        self.main_layout.addLayout(self.cards_layout)

        # ===== Chart Frame =====
        chart_frame = QFrame()
        chart_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e5e5e5;
                border-radius: 12px;
                padding: 24px;
            }
        """)

        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.setSpacing(16)

        chart_title = QLabel("Revenue Trend - Last 7 Days")
        chart_title.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #1a1a1a;
        """)
        chart_layout.addWidget(chart_title)

        self.figure = Figure(figsize=(10, 4), facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)

        self.main_layout.addWidget(chart_frame)
        self.main_layout.addStretch()

        self.load_chart()

        # Set up auto-refresh timer (refreshes every 5 seconds)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(5000)  # 5000 ms = 5 seconds

    def create_cards(self):
        """Create or update earnings cards"""
        # Clear existing cards if any
        for i in reversed(range(self.cards_layout.count())):
            widget = self.cards_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.card_labels.clear()

        def create_card(name, value, key):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: white;
                    border: 1px solid #e5e5e5;
                    border-radius: 12px;
                    padding: 20px;
                }
                QFrame:hover {
                    border: 1px solid #007bff;
                    box-shadow: 0 2px 8px rgba(0, 123, 255, 0.1);
                }
            """)

            vbox = QVBoxLayout(card)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.setSpacing(0)

            name_lbl = QLabel(name)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            name_lbl.setStyleSheet("""
                font-size: 13px; 
                font-weight: 600; 
                color: #666;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border: none;
            """)

            value_lbl = QLabel(value)
            value_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
            value_lbl.setStyleSheet("""
                font-size: 28px; 
                font-weight: bold; 
                color: #007bff;
                border: none;
            """)

            vbox.addWidget(name_lbl)
            vbox.addStretch()
            vbox.addWidget(value_lbl)

            # Store reference to value label
            self.card_labels[key] = value_lbl

            return card

        # ===== DB Queries =====
        daily = safe_query("SELECT IFNULL(SUM(total),0) AS total FROM transactions WHERE DATE(created_at)=CURDATE();")
        weekly = safe_query(
            "SELECT IFNULL(SUM(total),0) AS total FROM transactions WHERE created_at>=CURDATE()-INTERVAL 7 DAY;")
        monthly = safe_query(
            "SELECT IFNULL(SUM(total),0) AS total FROM transactions WHERE created_at>=CURDATE()-INTERVAL 30 DAY;")
        total = safe_query("SELECT IFNULL(SUM(total),0) AS total FROM transactions;")

        # Handle None results safely
        daily_val = float(daily['total']) if daily and daily.get('total') is not None else 0.0
        weekly_val = float(weekly['total']) if weekly and weekly.get('total') is not None else 0.0
        monthly_val = float(monthly['total']) if monthly and monthly.get('total') is not None else 0.0
        total_val = float(total['total']) if total and total.get('total') is not None else 0.0

        cards = [
            ("Today", f"₱{daily_val:,.2f}", "today"),
            ("Last 7 Days", f"₱{weekly_val:,.2f}", "weekly"),
            ("Last 30 Days", f"₱{monthly_val:,.2f}", "monthly"),
            ("All Time", f"₱{total_val:,.2f}", "total")
        ]

        for name, value, key in cards:
            self.cards_layout.addWidget(create_card(name, value, key))

    def refresh(self):
        """Refresh all earnings data - called automatically every 5 seconds"""
        # Update card values
        daily = safe_query("SELECT IFNULL(SUM(total),0) AS total FROM transactions WHERE DATE(created_at)=CURDATE();")
        weekly = safe_query(
            "SELECT IFNULL(SUM(total),0) AS total FROM transactions WHERE created_at>=CURDATE()-INTERVAL 7 DAY;")
        monthly = safe_query(
            "SELECT IFNULL(SUM(total),0) AS total FROM transactions WHERE created_at>=CURDATE()-INTERVAL 30 DAY;")
        total = safe_query("SELECT IFNULL(SUM(total),0) AS total FROM transactions;")

        # Handle None results safely
        daily_val = float(daily['total']) if daily and daily.get('total') is not None else 0.0
        weekly_val = float(weekly['total']) if weekly and weekly.get('total') is not None else 0.0
        monthly_val = float(monthly['total']) if monthly and monthly.get('total') is not None else 0.0
        total_val = float(total['total']) if total and total.get('total') is not None else 0.0

        # Update labels
        if "today" in self.card_labels:
            self.card_labels["today"].setText(f"₱{daily_val:,.2f}")
        if "weekly" in self.card_labels:
            self.card_labels["weekly"].setText(f"₱{weekly_val:,.2f}")
        if "monthly" in self.card_labels:
            self.card_labels["monthly"].setText(f"₱{monthly_val:,.2f}")
        if "total" in self.card_labels:
            self.card_labels["total"].setText(f"₱{total_val:,.2f}")

        # Refresh chart
        self.load_chart()

    def load_chart(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        rows = safe_query("""
            SELECT DATE(created_at) AS day, SUM(total) AS total
            FROM transactions
            WHERE created_at >= CURDATE() - INTERVAL 7 DAY
            GROUP BY day
            ORDER BY day;
        """, fetch="all") or []

        days = [str(r["day"]) for r in rows]
        totals = [float(r["total"]) for r in rows]

        # Modern chart styling
        bars = ax.bar(days, totals, color="#007bff", alpha=0.8, edgecolor='none')

        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'₱{height:,.0f}',
                    ha='center', va='bottom', fontsize=9, color='#666')

        ax.set_xlabel("Date", fontsize=11, color='#666', fontweight='500')
        ax.set_ylabel("Earnings (₱)", fontsize=11, color='#666', fontweight='500')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#e5e5e5')
        ax.spines['bottom'].set_color('#e5e5e5')
        ax.tick_params(colors='#666', labelsize=9)
        ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)

        # Rotate x-axis labels for better readability
        ax.tick_params(axis='x', rotation=45)

        self.figure.tight_layout()
        self.canvas.draw()

    def closeEvent(self, event):
        """Stop timer when widget is closed"""
        self.refresh_timer.stop()
        event.accept()