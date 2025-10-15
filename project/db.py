# db.py
import pymysql
import hashlib

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "techstore_pos"
}

def initialize_database():
    """
    Automatically create database and tables if they don't exist.
    This runs once when the application starts.
    """
    conn = None
    try:
        # Connect without specifying database to create it if needed
        conn = pymysql.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = conn.cursor()

        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        print(f"✓ Database '{DB_CONFIG['database']}' is ready.")

        # Switch to the database
        cursor.execute(f"USE {DB_CONFIG['database']}")

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('admin', 'cashier') NOT NULL,
                full_name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create products table with CHECK constraint
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                barcode VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                category VARCHAR(50),
                price DECIMAL(10, 2) NOT NULL,
                stock INT NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)

        # Create transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                transaction_date DATETIME NOT NULL,
                cashier_id INT NOT NULL,
                cashier_name VARCHAR(100),
                total_amount DECIMAL(10, 2) NOT NULL,
                amount_paid DECIMAL(10, 2) NOT NULL,
                change_amount DECIMAL(10, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cashier_id) REFERENCES users(id)
            )
        """)

        # Create transaction_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transaction_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                transaction_id INT NOT NULL,
                product_id INT NOT NULL,
                product_name VARCHAR(100) NOT NULL,
                product_barcode VARCHAR(50),
                quantity INT NOT NULL,
                unit_price DECIMAL(10, 2) NOT NULL,
                subtotal DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Create receipts table for storing receipt data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                transaction_id INT NOT NULL,
                receipt_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        print("✓ All tables created successfully.")

        # Create default admin user if it doesn't exist
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            hashed_password = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("""
                INSERT INTO users (username, password, role, full_name) 
                VALUES (%s, %s, %s, %s)
            """, ("admin", hashed_password, "admin", "System Administrator"))
            conn.commit()
            print("✓ Default admin user created (username: admin, password: admin123)")

        cursor.close()

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise
    finally:
        if conn:
            conn.close()

def safe_query(query, params=None, fetch="one"):
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
        cursor = conn.cursor()
        print(f"DEBUG: Executing query: {query} | params={params}")
        cursor.execute(query, params or ())

        if fetch == "all":
            result = cursor.fetchall()
        else:
            result = cursor.fetchone()

        conn.commit()
        return result
    except Exception as e:
        print("❌ Exception during DB query:", e)
        return [] if fetch == "all" else None
    finally:
        if conn:
            conn.close()

def validate_product_price(price):
    """Validate that product price is greater than zero"""
    try:
        price_float = float(price)
        return price_float > 0
    except (ValueError, TypeError):
        return False

def get_transaction_details(transaction_id):
    """Get complete transaction details including all purchased items"""
    transaction = safe_query(
        "SELECT * FROM transactions WHERE id = %s",
        (transaction_id,),
        fetch="one"
    )

    if transaction:
        items = safe_query(
            "SELECT * FROM transaction_items WHERE transaction_id = %s",
            (transaction_id,),
            fetch="all"
        )
        transaction['items'] = items

    return transaction

def get_daily_sales_report(date):
    """
    Get detailed daily sales report with all transaction details.
    Returns: dict with transactions list, total_sales, and transaction_count
    """
    transactions = safe_query("""
        SELECT t.id, t.transaction_date, t.cashier_name, 
               t.total_amount, t.amount_paid, t.change_amount,
               GROUP_CONCAT(
                   CONCAT(ti.product_name, ' (', ti.quantity, 'x @ ₱', ti.unit_price, ')') 
                   SEPARATOR ', '
               ) as items_summary
        FROM transactions t
        LEFT JOIN transaction_items ti ON t.id = ti.transaction_id
        WHERE DATE(t.transaction_date) = %s
        GROUP BY t.id, t.transaction_date, t.cashier_name, 
                 t.total_amount, t.amount_paid, t.change_amount
        ORDER BY t.transaction_date
    """, (date,), fetch="all")

    total_sales = sum(float(t['total_amount']) for t in transactions) if transactions else 0

    return {
        'transactions': transactions,
        'total_sales': total_sales,
        'transaction_count': len(transactions),
        'date': date
    }

def get_all_transactions_detailed():
    """Get all transactions with summary for history view"""
    return safe_query("""
        SELECT t.id, t.transaction_date, t.cashier_name, 
               t.total_amount, t.amount_paid, t.change_amount,
               GROUP_CONCAT(
                   CONCAT(ti.product_name, ' (', ti.quantity, 'x @ ₱', ti.unit_price, ')') 
                   SEPARATOR ', '
               ) as items_summary
        FROM transactions t
        LEFT JOIN transaction_items ti ON t.id = ti.transaction_id
        GROUP BY t.id, t.transaction_date, t.cashier_name, 
                 t.total_amount, t.amount_paid, t.change_amount
        ORDER BY t.transaction_date DESC
    """, fetch="all")

def save_transaction_with_items(cashier_id, cashier_name, items, total_amount, amount_paid, change_amount):
    """
    Save complete transaction with all items.
    Returns: transaction_id if successful, None otherwise
    """
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO transactions 
            (transaction_date, cashier_id, cashier_name, total_amount, amount_paid, change_amount) 
            VALUES (NOW(), %s, %s, %s, %s, %s)
        """, (cashier_id, cashier_name, total_amount, amount_paid, change_amount))

        transaction_id = cursor.lastrowid

        for item in items:
            cursor.execute("""
                INSERT INTO transaction_items 
                (transaction_id, product_id, product_name, product_barcode, 
                 quantity, unit_price, subtotal) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                transaction_id,
                item['id'],
                item['name'],
                item.get('barcode', ''),
                item['qty'],
                item['price'],
                item['subtotal']
            ))

            cursor.execute("""
                UPDATE products 
                SET stock = stock - %s 
                WHERE id = %s
            """, (item['qty'], item['id']))

        # Save receipt data
        receipt_data = {
            'transaction_id': str(transaction_id).zfill(10),
            'date': datetime.datetime.now().strftime("%Y-%m-%d"),
            'time': datetime.datetime.now().strftime("%H:%M:%S"),
            'cashier': cashier_name,
            'items': items,
            'subtotal': sum(item['subtotal'] for item in items),
            'tax': sum(item['subtotal'] for item in items) * 0.12,
            'total': total_amount,
            'payment': amount_paid,
            'change': change_amount
        }
        cursor.execute("""
            INSERT INTO receipts (transaction_id, receipt_data, created_at)
            VALUES (%s, %s, NOW())
        """, (transaction_id, json.dumps(receipt_data)))

        conn.commit()
        print(f"✓ Transaction {transaction_id} saved successfully with {len(items)} items")
        return transaction_id

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error saving transaction: {e}")
        return None
    finally:
        if conn:
            conn.close()

# Initialize database when module is imported
try:
    initialize_database()
except Exception as e:
    print(f"❌ Failed to initialize database: {e}")
    print("Please make sure MySQL/XAMPP is running and try again.")