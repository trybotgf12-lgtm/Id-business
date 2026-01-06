import sqlite3
from config import DB_FILE

class Database:
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_file, check_same_thread=False)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # User Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                balance REAL DEFAULT 0.0,
                currency TEXT DEFAULT 'INR',
                is_authorized BOOLEAN DEFAULT 0,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deg_coins REAL DEFAULT 0.0,
                referred_by INTEGER DEFAULT NULL,
                total_referrals INTEGER DEFAULT 0,
                total_coins_earned REAL DEFAULT 0.0,
                discount REAL DEFAULT 0.0
            )
        ''')
        
        # Categories Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                discount REAL DEFAULT 0.0
            )
        ''')
        
        # Products Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')

        # Stock Table (Accounts/Data)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                data TEXT NOT NULL,
                is_sold BOOLEAN DEFAULT 0,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')

        # Orders Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                data TEXT,
                amount REAL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # App Config Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    # --- User Methods ---
    def add_user(self, user_id, username, full_name, referrer_id=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if cursor.fetchone():
                return
            
            cursor.execute("INSERT INTO users (user_id, username, full_name, referred_by) VALUES (?, ?, ?, ?)", 
                         (user_id, username, full_name, referrer_id))
            
            if referrer_id:
                cursor.execute("UPDATE users SET total_referrals = total_referrals + 1 WHERE user_id = ?", (referrer_id,))
            
            conn.commit()
        finally:
            conn.close()

    def get_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return cursor.fetchone()
        finally:
            conn.close()
            
    def add_balance(self, user_id, amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
        finally:
            conn.close()
            
    def get_balance(self, user_id):
        user = self.get_user(user_id)
        return user[3] if user else 0.0

    def set_balance(self, user_id, amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
        finally:
            conn.close()

    def get_all_user_balances(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id, username, full_name, balance FROM users")
            return cursor.fetchall()
        finally:
            conn.close()

    def clear_all_user_balances(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET balance = 0")
            conn.commit()
        finally:
            conn.close()

    def get_user_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*), SUM(balance) FROM users")
            row = cursor.fetchone()
            return {"total_users": row[0] or 0, "total_balance": row[1] or 0}
        finally:
            conn.close()

    def set_currency(self, user_id, currency):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET currency = ? WHERE user_id = ?", (currency, user_id))
            conn.commit()
        finally:
            conn.close()

    def get_user_ids(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id FROM users")
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_user_orders(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                SELECT o.order_date, p.name, o.amount, o.data
                FROM orders o
                JOIN products p ON o.product_id = p.id
                WHERE o.user_id = ?
                ORDER BY o.order_date DESC
            """
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    # --- Shop Methods ---
    def add_category(self, name):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO categories (name, discount) VALUES (?, 0.0)", (name,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()

    def delete_category(self, cat_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM stock WHERE product_id IN (SELECT id FROM products WHERE category_id = ?)", (cat_id,))
            cursor.execute("DELETE FROM products WHERE category_id = ?", (cat_id,))
            cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
            conn.commit()
            return True
        finally:
            conn.close()
            
    def get_categories(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM categories")
            return cursor.fetchall()
        finally:
            conn.close()

    def get_category(self, cat_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM categories WHERE id = ?", (cat_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def get_active_categories(self, is_admin=False):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if is_admin:
                 cursor.execute("SELECT id, name FROM categories")
            else:
                query = """
                    SELECT DISTINCT c.id, c.name 
                    FROM categories c
                    JOIN products p ON c.id = p.category_id
                    JOIN stock s ON p.id = s.product_id
                    WHERE s.is_sold = 0
                """
                cursor.execute(query)
            return cursor.fetchall()
        finally:
            conn.close()
            
    def add_product(self, category_id, name, description, price):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO products (category_id, name, description, price) VALUES (?, ?, ?, ?)", (category_id, name, description, price))
            conn.commit()
        finally:
            conn.close()

    def get_products(self, category_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM products WHERE category_id = ?", (category_id,))
            return cursor.fetchall()
        finally:
            conn.close()

    def get_active_products(self, category_id, is_admin=False):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if is_admin:
                query = """
                    SELECT p.*, c.discount as cat_discount
                    FROM products p
                    JOIN categories c ON p.category_id = c.id
                    WHERE p.category_id = ?
                """
                cursor.execute(query, (category_id,))
            else:
                query = """
                    SELECT DISTINCT p.*, c.discount as cat_discount
                    FROM products p
                    JOIN categories c ON p.category_id = c.id
                    JOIN stock s ON p.id = s.product_id
                    WHERE p.category_id = ? AND s.is_sold = 0
                """
                cursor.execute(query, (category_id,))
            return cursor.fetchall()
        finally:
            conn.close()
            
    def get_product(self, product_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def add_stock(self, product_id, data):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO stock (product_id, data) VALUES (?, ?)", (product_id, data))
            conn.commit()
        finally:
            conn.close()
            
    def get_stock_count(self, product_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM stock WHERE product_id = ? AND is_sold = 0", (product_id,))
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def delete_unsold_stock(self, product_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM stock WHERE product_id = ? AND is_sold = 0", (product_id,))
            rows = cursor.rowcount
            conn.commit()
            return rows
        finally:
            conn.close()

    def update_price(self, product_id, new_price):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE products SET price = ? WHERE id = ?", (new_price, product_id))
            conn.commit()
        finally:
            conn.close()

    def set_authorized(self, user_id, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            val = 1 if status else 0
            cursor.execute("UPDATE users SET is_authorized = ? WHERE user_id = ?", (val, user_id))
            conn.commit()
        finally:
            conn.close()

    def set_discount(self, user_id, discount):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET discount = ? WHERE user_id = ?", (discount, user_id))
            conn.commit()
        finally:
            conn.close()

    def set_category_discount(self, cat_id, discount):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE categories SET discount = ? WHERE id = ?", (discount, cat_id))
            conn.commit()
        finally:
            conn.close()

    def get_category_discount(self, cat_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT discount FROM categories WHERE id = ?", (cat_id,))
            res = cursor.fetchone()
            return res[0] if res else 0.0
        finally:
            conn.close()

    def get_discount(self, user_id):
        user = self.get_user(user_id)
        if user and len(user) > 11:
            return user[11]
        return 0.0

    def buy_item(self, user_id, product_id, quantity=1):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT balance, is_authorized FROM users WHERE user_id = ?", (user_id,))
            user_res = cursor.fetchone()
            if not user_res: return None, "User not found"
            
            balance, is_auth = user_res
            
            cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
            price = cursor.fetchone()[0]
            
            cursor.execute("SELECT discount FROM users WHERE user_id = ?", (user_id,))
            disc_res = cursor.fetchone()
            discount = disc_res[0] if disc_res else 0.0
            
            final_price_per_item = price
            if discount > 0:
                final_price_per_item = price * (1 - discount / 100)
                
            total_price = final_price_per_item * quantity
            
            if not is_auth and balance < total_price:
                return None, f"Insufficient balance."
            
            cursor.execute("SELECT id, data FROM stock WHERE product_id = ? AND is_sold = 0 LIMIT ?", (product_id, quantity))
            items = cursor.fetchall()
            
            if len(items) < quantity:
                return None, f"Insufficient stock."
            
            purchased_data = []
            for item in items:
                stock_id, data = item
                purchased_data.append(data)
                cursor.execute("UPDATE stock SET is_sold = 1 WHERE id = ?", (stock_id,))
                cursor.execute("INSERT INTO orders (user_id, product_id, data, amount) VALUES (?, ?, ?, ?)", (user_id, product_id, data, final_price_per_item))
            
            if not is_auth:
                cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (total_price, user_id))
            
            conn.commit()
            return (purchased_data[0] if quantity == 1 else purchased_data), "Success"
        except Exception as e:
            conn.rollback()
            return None, str(e)

    def get_config(self, key):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT value FROM app_config WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def set_config(self, key, value):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT OR REPLACE INTO app_config (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()
        finally:
            conn.close()
    
    def add_deg_coins(self, user_id, amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET deg_coins = deg_coins + ?, total_coins_earned = total_coins_earned + ? WHERE user_id = ?", 
                         (amount, amount, user_id))
            conn.commit()
        finally:
            conn.close()
    
    def get_referral_stats(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT deg_coins, total_referrals, total_coins_earned FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            if result:
                return {'deg_coins': result[0], 'total_referrals': result[1], 'total_coins_earned': result[2]}
            return {'deg_coins': 0.0, 'total_referrals': 0, 'total_coins_earned': 0.0}
        finally:
            conn.close()

db = Database()
