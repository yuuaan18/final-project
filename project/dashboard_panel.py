from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QSizePolicy, QSpacerItem, QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QHeaderView
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from db import safe_query
import datetime


class DashboardPanel(QWidget):
    def __init__(self, username, role):
        super().__init__()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(15)

        # Default chart view
        self.current_view = "Daily"

        # Initialize the dashboard
        self.load_dashboard()

        # Set up auto-refresh timer (refreshes every 5 seconds)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_dashboard)
        self.refresh_timer.start(5000)  # 5000 ms = 5 seconds

        # ✅ Apply QSS
        try:
            self.setStyleSheet(open("qss/dashboard.qss").read())
        except Exception as e:
            print(f"⚠️ Could not load dashboard.qss: {e}")

    def load_dashboard(self):
        """Load all dashboard content"""
        # Clear existing layout
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

        # ===== Page Header =====
        header_layout = QVBoxLayout()
        page_title = QLabel("Dashboard")
        page_subtitle = QLabel("Overview of store performance and activities")
        page_title.setStyleSheet("font-size: 22px; font-weight: bold; margin-top: 15px;")
        page_subtitle.setStyleSheet("font-size: 13px; color: gray; margin-bottom: 10px;")
        header_layout.addWidget(page_title)
        header_layout.addWidget(page_subtitle)
        self.main_layout.addLayout(header_layout)

        # ===== Get Data From DB =====
        today = datetime.date.today()
        first_day = today.replace(day=1)

        today_sales = (safe_query(
            "SELECT IFNULL(SUM(total), 0) AS total FROM transactions WHERE DATE(created_at) = CURDATE();"
        ) or {"total": 0})["total"]

        monthly_sales = (safe_query(
            "SELECT IFNULL(SUM(total), 0) AS total FROM transactions WHERE created_at >= %s;",
            (first_day,)
        ) or {"total": 0})["total"]

        total_products = (safe_query(
            "SELECT COUNT(*) AS cnt FROM products;"
        ) or {"cnt": 0})["cnt"]

        transactions_count = (safe_query(
            "SELECT COUNT(*) AS cnt FROM transactions;"
        ) or {"cnt": 0})["cnt"]

        # ===== Top Stats Row =====
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        stats_row.addWidget(self.create_stat_card("Today's Sales", f"₱{today_sales:,.2f}"))
        stats_row.addWidget(self.create_stat_card("Monthly Sales", f"₱{monthly_sales:,.2f}"))
        stats_row.addWidget(self.create_stat_card("Total Products", f"{total_products:,}"))
        stats_row.addWidget(self.create_stat_card("Transactions", f"{transactions_count:,}"))
        self.main_layout.addLayout(stats_row)

        # ===== Chart View Selector =====
        selector_layout = QHBoxLayout()
        selector_label = QLabel("View:")
        selector_label.setStyleSheet("font-size: 14px; font-weight: bold;")

        self.view_combo = QComboBox()
        self.view_combo.addItems(["Daily", "Weekly", "Monthly", "Yearly"])
        self.view_combo.setCurrentText(self.current_view)
        self.view_combo.currentTextChanged.connect(self.on_view_changed)
        self.view_combo.setStyleSheet("""
            QComboBox {
                padding: 5px 10px;
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                background-color: white;
                color: black;
                font-size: 13px;
                min-width: 120px;
            }
            QComboBox:hover {
                border: 1px solid #007bff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid black;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #007bff;
                selection-color: white;
                border: 1px solid #dcdcdc;
            }
        """)

        selector_layout.addWidget(selector_label)
        selector_layout.addWidget(self.view_combo)
        selector_layout.addStretch()
        self.main_layout.addLayout(selector_layout)

        # ===== Charts Row =====
        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)

        # Get chart data based on current view
        sales_data = self.get_sales_data(self.current_view)
        revenue_data = self.get_revenue_data(self.current_view)

        # Sales Chart (Bar)
        sales_chart = self.create_chart(
            sales_data["labels"],
            sales_data["values"],
            f"{self.current_view} Sales",
            chart_type="bar"
        )
        charts_row.addWidget(sales_chart)

        # Revenue Chart (Line)
        revenue_chart = self.create_chart(
            revenue_data["labels"],
            revenue_data["values"],
            f"{self.current_view} Revenue",
            chart_type="line"
        )
        charts_row.addWidget(revenue_chart)

        self.main_layout.addLayout(charts_row)

        # ===== Recent Activity =====
        activity_frame = QFrame()
        activity_layout = QVBoxLayout(activity_frame)
        activity_title = QLabel("Recent Activity")
        activity_title.setObjectName("sectionTitle")
        activity_layout.addWidget(activity_title)

        recent_sales = safe_query(
            """
            SELECT 'Sale completed' as activity,
                   CONCAT('₱', t.total) as amount,
                   t.created_at,
                   u.username as user
            FROM transactions t
            JOIN users u ON t.user_id = u.id
            ORDER BY t.created_at DESC
            LIMIT 10;
            """,
            fetch="all"
        ) or []

        table = QTableWidget(len(recent_sales), 4)
        table.setHorizontalHeaderLabels(["Activity", "Amount", "Time", "User"])
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        table.setStyleSheet("""
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

        for row, sale in enumerate(recent_sales):
            table.setRowHeight(row, 35)
            table.setItem(row, 0, QTableWidgetItem(sale["activity"]))
            table.setItem(row, 1, QTableWidgetItem(sale["amount"]))
            table.setItem(row, 2, QTableWidgetItem(str(sale["created_at"])))
            table.setItem(row, 3, QTableWidgetItem(sale["user"]))

        activity_layout.addWidget(table)
        self.main_layout.addWidget(activity_frame)

    def on_view_changed(self, view):
        """Handle view selection change"""
        self.current_view = view
        self.refresh_timer.stop()  # Stop timer during refresh
        self.load_dashboard()
        self.refresh_timer.start(5000)  # Restart timer

    def get_sales_data(self, view):
        """Get sales data based on view type"""
        if view == "Daily":
            # Last 7 days
            data = safe_query(
                """
                SELECT DATE(created_at) as period, SUM(total) as total
                FROM transactions
                WHERE created_at >= CURDATE() - INTERVAL 7 DAY
                GROUP BY period
                ORDER BY period;
                """,
                fetch="all"
            ) or []
            labels = [str(row["period"]) for row in data]
            values = [float(row["total"]) for row in data]

        elif view == "Weekly":
            # Last 8 weeks
            data = safe_query(
                """
                SELECT YEARWEEK(created_at) as period, SUM(total) as total
                FROM transactions
                WHERE created_at >= CURDATE() - INTERVAL 8 WEEK
                GROUP BY period
                ORDER BY period;
                """,
                fetch="all"
            ) or []
            labels = [f"W{str(row['period'])[-2:]}" for row in data]
            values = [float(row["total"]) for row in data]

        elif view == "Monthly":
            # Last 12 months
            data = safe_query(
                """
                SELECT DATE_FORMAT(created_at, '%%Y-%%m') as period, SUM(total) as total
                FROM transactions
                WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                GROUP BY DATE_FORMAT(created_at, '%%Y-%%m')
                ORDER BY period;
                """,
                fetch="all"
            ) or []
            labels = [row["period"] for row in data]
            values = [float(row["total"]) for row in data]

        else:  # Yearly
            # Last 5 years
            data = safe_query(
                """
                SELECT YEAR(created_at) as period, SUM(total) as total
                FROM transactions
                WHERE created_at >= CURDATE() - INTERVAL 5 YEAR
                GROUP BY period
                ORDER BY period;
                """,
                fetch="all"
            ) or []
            labels = [str(row["period"]) for row in data]
            values = [float(row["total"]) for row in data]

        return {"labels": labels, "values": values}

    def get_revenue_data(self, view):
        """Get revenue data based on view type (same as sales for now)"""
        return self.get_sales_data(view)

    def refresh_dashboard(self):
        """Refresh dashboard data"""
        self.load_dashboard()

    def clear_layout(self, layout):
        """Helper function to clear a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

    # ===== Helper Functions =====
    def create_stat_card(self, title, value):
        card = QFrame()
        card.setObjectName("statCard")
        layout = QVBoxLayout(card)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("statTitle")
        layout.addWidget(lbl_title, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        lbl_value = QLabel(value)
        lbl_value.setObjectName("statValue")
        layout.addWidget(lbl_value, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

        return card

    def create_chart(self, labels, values, title, chart_type="bar"):
        frame = QFrame()
        frame.setObjectName("chartCard")
        layout = QVBoxLayout(frame)

        fig, ax = plt.subplots(figsize=(4, 3))
        if values:
            if chart_type == "bar":
                ax.bar(labels, values, color="#007bff", alpha=0.7)
            else:
                ax.plot(labels, values, marker="o", color="#28a745", linewidth=2)

        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_ylabel("Amount (₱)", fontsize=10)

        # Fix overlapping x-axis labels
        plt.xticks(rotation=45, ha='right', fontsize=9)
        plt.yticks(fontsize=9)
        fig.tight_layout()

        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)

        plt.close(fig)
        return frame

    def closeEvent(self, event):
        """Stop timer when widget is closed"""
        self.refresh_timer.stop()
        event.accept()