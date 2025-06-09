import sqlite3
import os
import datetime

class DatabaseManager:
    """
    Manages all interactions with the SQLite database.
    This class is responsible for creating the database, defining table schemas,
    and providing methods for CRUD (Create, Read, Update, Delete) operations.
    It should not contain any GUI-specific code.
    """
    def __init__(self, db_path='data/store.db'):
        """
        Initializes the DatabaseManager with the path to the SQLite database file.
        Ensures the directory for the database exists.
        """
        self.db_path = db_path
        # Ensure the directory for the database file exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def _get_connection(self):
        """
        Internal helper method to establish a connection to the database.
        Returns a SQLite connection object.
        """
        conn = sqlite3.connect(self.db_path)
        # Configure connection to return rows as dictionaries for easier access by column name
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_db(self):
        """
        Initializes the database by creating all necessary tables if they do not already exist.
        This method is called once when the application starts.
        Handles schema evolution for existing databases (e.g., adding new columns).
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 1. Products Table: Stores details about each inventory item
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                item_no TEXT PRIMARY KEY,           -- Unique identifier for the item (e.g., SKU)
                item_name TEXT NOT NULL,          -- Name of the product
                description TEXT,                 -- Detailed description
                unit TEXT,                        -- Unit of measurement (e.g., 'pcs', 'kg', 'pack')
                supplier_price REAL,              -- Cost price per unit from supplier
                selling_price REAL,               -- Selling price per unit to customer
                current_stock INTEGER DEFAULT 0,  -- Current quantity in stock
                reorder_alert INTEGER DEFAULT 0,  -- 0 for No, 1 for Yes (derived from current_stock < reorder_level)
                reorder_qty INTEGER DEFAULT 5     -- Suggested quantity to reorder when stock is low
            )
        ''')

        # Add 'is_active' column if it doesn't exist (schema evolution)
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN is_active INTEGER DEFAULT 1")
            conn.commit()
            print("Added 'is_active' column to 'products' table.")
        except sqlite3.OperationalError as e:
            if "duplicate column name: is_active" in str(e):
                # Column already exists, which is fine
                pass
            else:
                raise e # Re-raise unexpected errors


        # 2. Sales Table: Logs each completed sales transaction
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique ID for each sale
                sale_date TEXT NOT NULL,                 -- Date of the sale (YYYY-MM-DD)
                sale_time TEXT NOT NULL,                 -- Time of the sale (HH:MM:SS)
                total_amount REAL NOT NULL,              -- Grand total amount of the sale
                payment_type TEXT NOT NULL,              -- 'Cash' or 'Credit'
                customer_name TEXT,                      -- Customer name (optional, especially for cash sales)
                notes TEXT                               -- Any additional notes for the sale
            )
        ''')

        # 3. Sale Items Table: Details of items included in each sale (linked to sales table)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_items (
                sale_item_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique ID for each item in a sale
                sale_id INTEGER NOT NULL,                       -- Foreign key to the sales table
                item_no TEXT NOT NULL,                          -- Foreign key to the products table
                quantity_sold INTEGER NOT NULL,                 -- Quantity of this item sold in this transaction
                selling_price_at_sale REAL NOT NULL,            -- Selling price at the time of sale (for historical accuracy)
                supplier_price_at_sale REAL NOT NULL,           -- Supplier price at the time of sale (for COGS calculation)
                FOREIGN KEY (sale_id) REFERENCES sales(sale_id),
                FOREIGN KEY (item_no) REFERENCES products(item_no)
            )
        ''')

        # 4. Stock In Log Table: Records incoming inventory (e.g., from suppliers)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_in_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique ID for each stock-in event
                item_no TEXT NOT NULL,                     -- Foreign key to the products table
                quantity_added INTEGER NOT NULL,           -- Quantity added to stock
                date TEXT NOT NULL,                        -- Date of stock-in (YYYY-MM-DD)
                time TEXT NOT NULL,                        -- Time of stock-in (HH:MM:SS)
                supplier_name TEXT,                        -- Name of the supplier
                notes TEXT,                                -- Any additional notes
                FOREIGN KEY (item_no) REFERENCES products(item_no)
            )
        ''')

        # 5. Credit Sales Table: Manages sales made on credit
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_sales (
                credit_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique ID for each credit sale
                sale_id INTEGER NOT NULL,                    -- Foreign key to the sales table
                customer_name TEXT NOT NULL,                 -- Name of the customer who bought on credit
                original_amount REAL NOT NULL,               -- Original total amount due for the credit sale
                amount_paid REAL DEFAULT 0.0,                -- Total amount paid so far
                balance REAL NOT NULL,                       -- Remaining balance due
                status TEXT NOT NULL,                        -- 'Unpaid', 'Partially Paid', 'Paid'
                due_date TEXT,                               -- Optional due date (YYYY-MM-DD)
                FOREIGN KEY (sale_id) REFERENCES sales(sale_id)
            )
        ''')

        # 6. Expenses Table: Tracks daily business expenses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                expense_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique ID for each expense
                date TEXT NOT NULL,                         -- Date of the expense (YYYY-MM-DD)
                time TEXT NOT NULL,                         -- Time of the expense (HH:MM:SS)
                category TEXT NOT NULL,                     -- Category of the expense (e.g., 'Rent', 'Utilities', 'Salaries')
                description TEXT,                           -- Description of the expense
                amount REAL NOT NULL                        -- Amount of the expense
            )
        ''')

        conn.commit()
        conn.close()

    # --- Basic CRUD Methods for Products (Examples) ---
    # You will add similar methods for all other tables as you build out managers.

    def add_product(self, item_no, item_name, description, unit, supplier_price, selling_price, current_stock, reorder_alert, reorder_qty, is_active=1):
        """
        Adds a new product to the database.
        Returns a tuple: (True/False, "message")
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO products (item_no, item_name, description, unit, supplier_price, selling_price, current_stock, reorder_alert, reorder_qty, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item_no, item_name, description, unit, supplier_price, selling_price, current_stock, reorder_alert, reorder_qty, is_active))
            conn.commit()
            return True, f"Product '{item_name}' (Item No: {item_no}) added successfully."
        except sqlite3.IntegrityError:
            return False, f"Error: Product with Item No. '{item_no}' already exists."
        except Exception as e:
            return False, f"An unexpected error occurred while adding product: {e}"
        finally:
            conn.close()

    def get_all_products(self, include_inactive=False):
        """Retrieves all products from the database, optionally including inactive ones."""
        conn = self._get_connection()
        cursor = conn.cursor()
        if include_inactive:
            cursor.execute("SELECT * FROM products")
        else:
            cursor.execute("SELECT * FROM products WHERE is_active = 1")
        products = cursor.fetchall()
        conn.close()
        # Convert rows to dictionaries for easier consumption by managers/UI
        return [dict(row) for row in products]

    def get_product_by_item_no(self, item_no):
        """Retrieves a single product by its item number."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE item_no = ?", (item_no,))
        product = cursor.fetchone()
        conn.close()
        return dict(product) if product else None

    def update_product_stock(self, item_no, quantity_change):
        """
        Updates the stock level of a product.
        quantity_change can be positive (stock in) or negative (stock out).
        Returns True/False based on success.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE products SET current_stock = current_stock + ? WHERE item_no = ?", (quantity_change, item_no))
            conn.commit()
            return True
        except Exception as e:
            print(f"An error occurred while updating stock for {item_no}: {e}")
            return False
        finally:
            conn.close()

    def delete_product(self, item_no):
        """
        Deletes a product from the database.
        Returns True/False based on success.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM products WHERE item_no = ?", (item_no,))
            conn.commit()
            return True
        except Exception as e:
            print(f"An error occurred while deleting product: {e}")
            return False
        finally:
            conn.close()

    def update_product_status(self, item_no, is_active):
        """
        Updates the active status of a product (1 for active, 0 for inactive).
        Returns a tuple: (True/False, "message")
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE products SET is_active = ? WHERE item_no = ?", (is_active, item_no))
            conn.commit()
            status_text = "activated" if is_active == 1 else "discontinued"
            return True, f"Product '{item_no}' has been {status_text}."
        except Exception as e:
            return False, f"Error updating status for product '{item_no}': {e}"
        finally:
            conn.close()

    def clear_all_products(self):
        """
        Deletes all records from the 'products' table.
        Use with extreme caution, as this will clear your entire inventory.
        Returns a tuple: (True/False, "message")
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM products")
            conn.commit()
            return True, "All inventory products cleared successfully."
        except Exception as e:
            conn.rollback()
            return False, f"An error occurred while clearing all products: {e}"
        finally:
            conn.close()

    # --- Placeholder for other table operations ---

    def add_sale(self, sale_data, sale_items_data):
        """Adds a new sales transaction and its items to the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Insert into sales table
            cursor.execute('''
                INSERT INTO sales (sale_date, sale_time, total_amount, payment_type, customer_name, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (sale_data['sale_date'], sale_data['sale_time'], sale_data['total_amount'],
                  sale_data['payment_type'], sale_data.get('customer_name'), sale_data.get('notes')))
            sale_id = cursor.lastrowid # Get the ID of the newly inserted sale

            # Insert into sale_items table
            for item in sale_items_data:
                cursor.execute('''
                    INSERT INTO sale_items (sale_id, item_no, quantity_sold, selling_price_at_sale, supplier_price_at_sale)
                    VALUES (?, ?, ?, ?, ?)
                ''', (sale_id, item['item_no'], item['quantity_sold'], item['selling_price_at_sale'], item['supplier_price_at_sale']))

            conn.commit()
            return sale_id
        except Exception as e:
            print(f"An error occurred while adding sale: {e}")
            conn.rollback() # Rollback changes if an error occurs
            return None
        finally:
            conn.close()

    def get_sales_by_date_range(self, start_date, end_date):
        """Retrieves sales within a specified date range."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sales WHERE sale_date BETWEEN ? AND ? ORDER BY sale_date, sale_time", (start_date, end_date))
        sales = cursor.fetchall()
        conn.close()
        return [dict(row) for row in sales]

    def add_expense(self, date, time, category, description, amount):
        """Adds a new expense to the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO expenses (date, time, category, description, amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (date, time, category, description, amount))
            conn.commit()
            return True
        except Exception as e:
            print(f"An error occurred while adding expense: {e}")
            return False
        finally:
            conn.close()

    def get_expenses_by_date_range(self, start_date, end_date):
        """Retrieves expenses within a specified date range."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date, time", (start_date, end_date))
        expenses = cursor.fetchall()
        conn.close()
        return [dict(row) for row in expenses]

    def add_stock_in_log(self, item_no, quantity_added, date, time, supplier_name, notes):
        """Logs a stock-in event."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO stock_in_log (item_no, quantity_added, date, time, supplier_name, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (item_no, quantity_added, date, time, supplier_name, notes))
            conn.commit()
            return True
        except Exception as e:
            print(f"An error occurred while logging stock-in: {e}")
            return False
        finally:
            conn.close()

    def get_stock_in_logs_by_date_range(self, start_date, end_date):
        """Retrieves stock-in logs within a specified date range."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stock_in_log WHERE date BETWEEN ? AND ? ORDER BY date, time", (start_date, end_date))
        logs = cursor.fetchall()
        conn.close()
        return [dict(row) for row in logs]

    def add_credit_sale(self, sale_id, customer_name, original_amount, balance, status, due_date=None):
        """Records a new credit sale."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO credit_sales (sale_id, customer_name, original_amount, balance, status, due_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (sale_id, customer_name, original_amount, balance, status, due_date))
            conn.commit()
            return True
        except Exception as e:
            print(f"An error occurred while adding credit sale: {e}")
            return False
        finally:
            conn.close()

    def update_credit_sale_payment(self, credit_id, amount_paid):
        """Updates the amount paid for a credit sale and adjusts the balance and status."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT original_amount, amount_paid FROM credit_sales WHERE credit_id = ?", (credit_id,))
            credit_sale = cursor.fetchone()
            if credit_sale:
                current_paid = credit_sale['amount_paid']
                original_amount = credit_sale['original_amount']
                new_total_paid = current_paid + amount_paid
                new_balance = original_amount - new_total_paid
                status = 'Unpaid'
                if new_balance <= 0:
                    status = 'Paid'
                    new_balance = 0 # Ensure balance doesn't go negative
                elif new_total_paid > 0:
                    status = 'Partially Paid'

                cursor.execute('''
                    UPDATE credit_sales
                    SET amount_paid = ?, balance = ?, status = ?
                    WHERE credit_id = ?
                ''', (new_total_paid, new_balance, status, credit_id))
                conn.commit()
                return True
            return False
        except Exception as e:
            print(f"An error occurred while updating credit sale payment: {e}")
            return False
        finally:
            conn.close()

    def get_all_credit_sales(self):
        """Retrieves all credit sales."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM credit_sales ORDER BY status, customer_name")
        credit_sales = cursor.fetchall()
        conn.close()
        return [dict(row) for row in credit_sales]

    def get_unpaid_credit_sales(self, customer_name=None):
        """Retrieves all unpaid or partially paid credit sales, optionally filtered by customer name."""
        conn = self._get_connection()
        cursor = conn.cursor()
        if customer_name:
            cursor.execute("SELECT * FROM credit_sales WHERE status != 'Paid' AND customer_name = ? ORDER BY customer_name, due_date", (customer_name,))
        else:
            cursor.execute("SELECT * FROM credit_sales WHERE status != 'Paid' ORDER BY customer_name, due_date")
        credit_sales = cursor.fetchall()
        conn.close()
        return [dict(row) for row in credit_sales]
