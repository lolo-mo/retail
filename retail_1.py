import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk # Import Image and ImageTk
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import math # Import math for ceil

# --- Database Manager Class ---
# This class handles all interactions with the SQLite database.
class DatabaseManager:
    def __init__(self, db_name="grocery_store.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()
        self._migrate_schema() # Call schema migration after table creation

    def _connect(self):
        """Establishes a connection to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {e}")

    def _create_tables(self):
        """Creates necessary tables if they don't exist."""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    item_no TEXT PRIMARY KEY,
                    item_name TEXT NOT NULL,
                    item_description TEXT,
                    unit TEXT,
                    supplier_price REAL,
                    selling_price REAL,
                    current_stock INTEGER DEFAULT 0,
                    reorder_level INTEGER DEFAULT 5,
                    reorder_qty INTEGER DEFAULT 0,
                    volume INTEGER DEFAULT 1,       -- Column for volume
                    interest INTEGER DEFAULT 0      -- New column for interest (whole number)
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_date TEXT NOT NULL,
                    total_amount REAL,
                    payment_type TEXT,
                    customer_name TEXT,
                    paid_amount REAL DEFAULT 0,
                    status TEXT DEFAULT 'Unpaid',
                    additional_charge REAL DEFAULT 0.0
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sale_items (
                    sale_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER,
                    item_no TEXT,
                    quantity INTEGER,
                    price_at_sale REAL,
                    subtotal REAL,
                    FOREIGN KEY (sale_id) REFERENCES sales(sale_id),
                    FOREIGN KEY (item_no) REFERENCES inventory(item_no)
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_in (
                    stock_in_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_no TEXT,
                    quantity INTEGER,
                    date_received TEXT,
                    supplier TEXT,
                    FOREIGN KEY (item_no) REFERENCES inventory(item_no)
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_date TEXT NOT NULL,
                    description TEXT,
                    amount REAL,
                    item_name TEXT
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to create tables: {e}")

    def _migrate_schema(self):
        """Performs necessary database schema migrations."""
        try:
            # Check if 'additional_charge' column exists in 'sales' table
            self.cursor.execute("PRAGMA table_info(sales)")
            columns = self.cursor.fetchall()
            column_names = [col[1] for col in columns]

            if 'additional_charge' not in column_names:
                self.cursor.execute("ALTER TABLE sales ADD COLUMN additional_charge REAL DEFAULT 0.0")
                self.conn.commit()
                print("Database schema migrated: Added 'additional_charge' column to 'sales' table.")
            
            # Check if 'item_name' column exists in 'expenses' table
            self.cursor.execute("PRAGMA table_info(expenses)")
            columns = self.cursor.fetchall()
            column_names_expenses = [col[1] for col in columns]

            if 'item_name' not in column_names_expenses:
                self.cursor.execute("ALTER TABLE expenses ADD COLUMN item_name TEXT")
                self.conn.commit()
                print("Database schema migrated: Added 'item_name' column to 'expenses' table.")

            # Check if 'volume' column exists in 'inventory' table
            self.cursor.execute("PRAGMA table_info(inventory)")
            columns = self.cursor.fetchall()
            column_names_inventory = [col[1] for col in columns]

            if 'volume' not in column_names_inventory:
                self.cursor.execute("ALTER TABLE inventory ADD COLUMN volume INTEGER DEFAULT 1")
                self.conn.commit()
                print("Database schema migrated: Added 'volume' column to 'inventory' table.")

            # Check if 'interest' column exists in 'inventory' table
            if 'interest' not in column_names_inventory:
                self.cursor.execute("ALTER TABLE inventory ADD COLUMN interest INTEGER DEFAULT 0")
                self.conn.commit()
                print("Database schema migrated: Added 'interest' column to 'inventory' table.")

        except sqlite3.Error as e:
            messagebox.showwarning("Database Migration Error", f"Failed to migrate schema: {e}")

    def add_item(self, item_data):
        """Adds a new item to the inventory."""
        try:
            # Added 'interest' to the INSERT statement
            self.cursor.execute('''
                INSERT INTO inventory (item_no, item_name, item_description, unit, supplier_price, selling_price, current_stock, reorder_level, reorder_qty, volume, interest)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item_data['item_no'], item_data['item_name'], item_data['item_description'], item_data['unit'],
                  item_data['supplier_price'], item_data['selling_price'], item_data['current_stock'],
                  item_data['reorder_level'], item_data['reorder_qty'], item_data['volume'], item_data['interest']))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Item Number already exists.")
            return False
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to add item: {e}")
            return False

    def update_item(self, item_no, item_data):
        """Updates an existing item in the inventory."""
        try:
            # Added 'interest' to the UPDATE statement
            self.cursor.execute('''
                UPDATE inventory SET
                    item_name = ?, item_description = ?, unit = ?, supplier_price = ?,
                    selling_price = ?, current_stock = ?, reorder_level = ?, reorder_qty = ?, volume = ?, interest = ?
                WHERE item_no = ?
            ''', (item_data['item_name'], item_data['item_description'], item_data['unit'],
                  item_data['supplier_price'], item_data['selling_price'], item_data['current_stock'],
                  item_data['reorder_level'], item_data['reorder_qty'], item_data['volume'], item_data['interest'], item_no))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to update item: {e}")
            return False
    
    def update_item_interest(self, item_no, new_interest):
        """Updates only the interest field for a specific item."""
        try:
            self.cursor.execute('UPDATE inventory SET interest = ? WHERE item_no = ?', (new_interest, item_no))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to update item interest: {e}")
            return False

    def update_item_volume(self, item_no, new_volume):
        """Updates only the volume field for a specific item."""
        try:
            self.cursor.execute('UPDATE inventory SET volume = ? WHERE item_no = ?', (new_volume, item_no))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to update item volume: {e}")
            return False

    def update_item_supplier_price(self, item_no, new_supplier_price):
        """Updates only the supplier_price field for a specific item."""
        try:
            self.cursor.execute('UPDATE inventory SET supplier_price = ? WHERE item_no = ?', (new_supplier_price, item_no))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to update item supplier price: {e}")
            return False

    def delete_item(self, item_no):
        """Deletes an item from the inventory."""
        try:
            self.cursor.execute('DELETE FROM inventory WHERE item_no = ?', (item_no,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to delete item: {e}")
            return False

    def get_all_items(self):
        """Retrieves all items from the inventory."""
        try:
            # Include 'volume' and 'interest' in the SELECT statement (now 11 fields)
            self.cursor.execute('SELECT item_no, item_name, item_description, unit, supplier_price, selling_price, current_stock, reorder_level, reorder_qty, volume, interest FROM inventory')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch items: {e}")
            return []

    def get_item_by_no_or_name(self, query):
        """Searches for items by item number or name."""
        try:
            # Include 'volume' and 'interest' in the SELECT statement
            self.cursor.execute('''
                SELECT item_no, item_name, item_description, unit, supplier_price, selling_price, current_stock, reorder_level, reorder_qty, volume, interest FROM inventory
                WHERE item_no LIKE ? OR item_name LIKE ?
            ''', (f'%{query}%', f'%{query}%'))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to search items: {e}")
            return []

    def get_item_by_item_no(self, item_no):
        """Retrieves a single item by its item number."""
        try:
            # Include 'volume' and 'interest' in the SELECT statement
            self.cursor.execute('SELECT item_no, item_name, item_description, unit, supplier_price, selling_price, current_stock, reorder_level, reorder_qty, volume, interest FROM inventory WHERE item_no = ?', (item_no,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch item by ID: {e}")
            return None

    def update_stock(self, item_no, quantity_change):
        """Updates the current stock of an item."""
        try:
            self.cursor.execute('UPDATE inventory SET current_stock = current_stock + ? WHERE item_no = ?',
                                (quantity_change, item_no))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to update stock: {e}")
            return False

    def record_stock_in(self, item_no, quantity, date_received, supplier):
        """Records a stock-in transaction."""
        try:
            self.cursor.execute('''
                INSERT INTO stock_in (item_no, quantity, date_received, supplier)
                VALUES (?, ?, ?, ?)
            ''', (item_no, quantity, date_received, supplier))
            self.conn.commit()
            self.update_stock(item_no, quantity) # Update inventory
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to record stock in: {e}")
            return False

    def get_all_stock_in_logs(self):
        """Retrieves all stock-in log entries."""
        try:
            # Modified query to include item_no and item_description
            self.cursor.execute('''
                SELECT si.stock_in_id, inv.item_no, inv.item_name, inv.item_description, si.quantity, si.date_received, si.supplier, inv.supplier_price
                FROM stock_in si
                JOIN inventory inv ON si.item_no = inv.item_no
                ORDER BY si.date_received DESC
            ''')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch stock in logs: {e}")
            return []

    def record_sale(self, total_amount, payment_type, customer_name, paid_amount, status, additional_charge, sale_items):
        """Records a new sale transaction."""
        try:
            self.cursor.execute('''
                INSERT INTO sales (sale_date, total_amount, payment_type, customer_name, paid_amount, status, additional_charge)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), total_amount, payment_type, customer_name, paid_amount, status, additional_charge))
            sale_id = self.cursor.lastrowid
            self.conn.commit()

            for item in sale_items:
                self.cursor.execute('''
                    INSERT INTO sale_items (sale_id, item_no, quantity, price_at_sale, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                ''', (sale_id, item['item_no'], item['quantity'], item['price_at_sale'], item['subtotal']))
                self.update_stock(item['item_no'], -item['quantity']) # Deduct from stock
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to record sale: {e}")
            self.conn.rollback() # Rollback if any error occurs
            return False

    def get_all_sales(self):
        """Retrieves all sales transactions."""
        try:
            # Changed order by to sale_id ASC
            self.cursor.execute('SELECT * FROM sales ORDER BY sale_id ASC')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch sales: {e}")
            return []

    def get_sale_details_for_display(self, sale_id):
        """Retrieves details of a specific sale including additional_charge."""
        try:
            self.cursor.execute('SELECT total_amount, additional_charge FROM sales WHERE sale_id = ?', (sale_id,))
            sale_summary = self.cursor.fetchone()

            self.cursor.execute('''
                SELECT inv.item_no, inv.item_name, inv.item_description, si.quantity, si.price_at_sale, si.subtotal
                FROM sale_items si
                JOIN inventory inv ON si.item_no = inv.item_no
                WHERE si.sale_id = ?
            ''', (sale_id,))
            sale_items = self.cursor.fetchall()
            return sale_summary, sale_items
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch sale details: {e}")
            return None, []

    def get_credit_sales(self):
        """Retrieves all credit sales (unpaid or partially paid)."""
        try:
            self.cursor.execute("SELECT * FROM sales WHERE payment_type = 'Credit' ORDER BY sale_date DESC")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch credit sales: {e}")
            return []

    def update_credit_sale_payment(self, sale_id, amount_paid):
        """Updates the paid amount for a credit sale."""
        try:
            self.cursor.execute('UPDATE sales SET paid_amount = paid_amount + ? WHERE sale_id = ?',
                                (amount_paid, sale_id))
            # Check if fully paid
            self.cursor.execute('SELECT total_amount, paid_amount FROM sales WHERE sale_id = ?', (sale_id,))
            total, paid = self.cursor.fetchone()
            if paid >= total:
                self.cursor.execute("UPDATE sales SET status = 'Paid' WHERE sale_id = ?", (sale_id,))
            else:
                self.cursor.execute("UPDATE sales SET status = 'Partially Paid' WHERE sale_id = ?", (sale_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to update credit sale payment: {e}")
            return False

    def add_expense(self, expense_data):
        """Adds a new expense."""
        try:
            # Updated INSERT statement to include 'item_name'
            self.cursor.execute('''
                INSERT INTO expenses (expense_date, item_name, description, amount)
                VALUES (?, ?, ?, ?)
            ''', (expense_data['expense_date'], expense_data['item_name'], expense_data['description'], expense_data['amount']))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to add expense: {e}")
            return False

    def get_expense_by_id(self, expense_id):
        """Retrieves a single expense by its ID."""
        try:
            self.cursor.execute('SELECT expense_id, expense_date, item_name, description, amount FROM expenses WHERE expense_id = ?', (expense_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch expense by ID: {e}")
            return None

    def update_expense(self, expense_id, expense_data):
        """Updates an existing expense."""
        try:
            self.cursor.execute('''
                UPDATE expenses SET
                    expense_date = ?, item_name = ?, description = ?, amount = ?
                WHERE expense_id = ?
            ''', (expense_data['expense_date'], expense_data['item_name'], expense_data['description'], expense_data['amount'], expense_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to update expense: {e}")
            return False

    def delete_expense(self, expense_id):
        """Deletes an expense."""
        try:
            self.cursor.execute('DELETE FROM expenses WHERE expense_id = ?', (expense_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to delete expense: {e}")
            return False

    def get_all_expenses(self):
        """Retrieves all expenses."""
        try:
            # Updated SELECT statement to include 'item_name'
            self.cursor.execute('SELECT expense_id, expense_date, item_name, description, amount FROM expenses ORDER BY expense_date DESC')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch expenses: {e}")
            return []

    def get_total_expenses(self, start_date=None, end_date=None):
        """Calculates total expenses within a date range."""
        try:
            query = "SELECT SUM(amount) FROM expenses"
            params = []
            if start_date and end_date:
                query += " WHERE expense_date BETWEEN ? AND ?"
                params = [start_date, end_date]
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()[0]
            return result if result is not None else 0.0
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to calculate total expenses: {e}")
            return 0.0

    def get_sales_summary(self, start_date=None, end_date=None):
        """
        Calculates:
        1. Total collected sales revenue (paid amounts).
        2. COGS based on selling price (sum of subtotals from sale_items).
        3. COGS based on original supplier price (per unit) for items sold.
        """
        try:
            # 1. Total Collected Revenue
            query_revenue = "SELECT SUM(CASE WHEN payment_type = 'Cash' THEN total_amount ELSE paid_amount END) FROM sales"
            params = []
            if start_date and end_date:
                query_revenue += " WHERE sale_date BETWEEN ? AND ?"
                params = [start_date, end_date]
            self.cursor.execute(query_revenue, params)
            total_revenue_collected = self.cursor.fetchone()[0] or 0.0

            # 2. COGS based on Selling Price (sum of subtotals, as per previous request)
            # This represents the sum of (selling_price * quantity_sold) from recorded sale_items
            query_cogs_selling_price_based = '''
                SELECT SUM(si.subtotal)
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.sale_id
            '''
            params_cogs_selling_price_based = []
            if start_date and end_date:
                query_cogs_selling_price_based += " WHERE s.sale_date BETWEEN ? AND ?"
                params_cogs_selling_price_based = [start_date, end_date]

            self.cursor.execute(query_cogs_selling_price_based, params_cogs_selling_price_based)
            cogs_selling_price_based = self.cursor.fetchone()[0] or 0.0

            # 3. COGS based on Supplier Price (per unit) for items sold
            # This represents the actual cost of goods sold based on their acquisition cost.
            cogs_supplier_price_based = 0.0
            query_supplier_cogs_items = '''
                SELECT si.quantity, inv.supplier_price, inv.volume
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.sale_id
                JOIN inventory inv ON si.item_no = inv.item_no
            '''
            params_supplier_cogs_items = []
            if start_date and end_date:
                query_supplier_cogs_items += " WHERE s.sale_date BETWEEN ? AND ?"
                params_supplier_cogs_items = [start_date, end_date]

            self.cursor.execute(query_supplier_cogs_items, params_supplier_cogs_items)
            sold_items_for_supplier_cogs = self.cursor.fetchall()

            for quantity, supplier_price_investment, volume in sold_items_for_supplier_cogs:
                # Ensure volume is at least 1 and not None to prevent division by zero or errors
                calculated_volume = max(1, volume if volume is not None else 1)
                per_unit_supplier_cost = supplier_price_investment / calculated_volume
                cogs_supplier_price_based += quantity * per_unit_supplier_cost

            return total_revenue_collected, cogs_selling_price_based, cogs_supplier_price_based
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to calculate sales summary: {e}")
            return 0.0, 0.0, 0.0

    def get_supplier_inventory_value(self):
        """
        Calculates the total value of current inventory based on Supplier Price (Per Unit).
        Supplier Price (Per Unit) = Supplier Price (Investment) / Volume
        """
        try:
            self.cursor.execute('''
                SELECT SUM(current_stock * (supplier_price * 1.0 / MAX(1, volume))) 
                FROM inventory
            ''')
            value = self.cursor.fetchone()[0]
            return value if value is not None else 0.0
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to calculate supplier inventory value: {e}")
            return 0.0
            
    def get_selling_inventory_value(self):
        """Calculates the total value of current inventory based on selling price."""
        try:
            self.cursor.execute('SELECT SUM(current_stock * selling_price) FROM inventory')
            value = self.cursor.fetchone()[0]
            return value if value is not None else 0.0
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to calculate selling inventory value: {e}")
            return 0.0

    def get_reorder_cost(self):
        """
        Calculates the total cost to re-order all flagged items based on
        (Re-Order QTY * Supplier Price (Per Unit)).
        """
        try:
            self.cursor.execute('''
                SELECT SUM(inv.reorder_qty * (inv.supplier_price * 1.0 / MAX(1, inv.volume)))
                FROM inventory inv
                WHERE inv.current_stock < inv.reorder_level
            ''')
            cost = self.cursor.fetchone()[0]
            return cost if cost is not None else 0.0
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to calculate re-order cost: {e}")
            return 0.0

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()

# --- Main Application Class ---
class GroceryStoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Grocery Store Management System")
        self.geometry("1200x950")

        self.db = DatabaseManager()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Load the logo image
        self.logo_image = None
        try:
            original_image = Image.open("SariSari__1_-removebg-preview.png")
            # Resize the image to a smaller size, e.g., 80x80 pixels
            resized_image = original_image.resize((80, 80), Image.Resampling.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(resized_image)
        except FileNotFoundError:
            messagebox.showwarning("Image Error", "Logo image 'SariSari__1_-removebg-preview.png' not found.")
        except Exception as e:
            messagebox.showwarning("Image Error", f"Error loading logo image: {e}")

        # Create tabs in desired order
        self.create_dashboard_tab()
        self.create_inventory_tab()
        self.create_pos_tab()
        self.create_stock_in_tab()
        self.create_stock_out_tab() # This is the sales log
        self.create_credit_sales_tab()
        self.create_profit_expenses_tab()
        self.create_pricing_tab() # New Pricing tab
        self.create_reports_tab()

        # Bind tab change event to refresh data
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        # Ensure database connection is closed on app exit
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_tab_change(self, event):
        """Refreshes data when a new tab is selected."""
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        if selected_tab == "Dashboard":
            self.refresh_dashboard()
        elif selected_tab == "Inventory Management":
            self.refresh_inventory_list()
        elif selected_tab == "POS":
            # POS typically doesn't need full refresh, but clear cart if needed
            pass
        elif selected_tab == "Stock In Log":
            self.refresh_stock_in_log()
        elif selected_tab == "Sales Log":
            self.refresh_sales_log()
        elif selected_tab == "Credit Sales":
            self.refresh_credit_sales_list()
        elif selected_tab == "Profit & Expenses":
            self.refresh_expenses_list()
            self.refresh_profit_summary()
            self.clear_expense_form() # Ensure the form is clear and buttons are reset on tab change
        elif selected_tab == "Pricing": # Refresh pricing tab
            self.refresh_pricing_list()
        elif selected_tab == "Reports":
            # Reports need explicit generation
            pass

    def _on_closing(self):
        """Handles application closing, ensuring database connection is closed."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.db.close()
            self.destroy()

    # --- Dashboard Tab ---
    def create_dashboard_tab(self):
        self.dashboard_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.dashboard_frame.columnconfigure(0, weight=1) # Column for Logo and Key Metrics
        self.dashboard_frame.columnconfigure(1, weight=1) # Column for Date/Time and Sales Statistics
        self.dashboard_frame.rowconfigure(1, weight=1) # Row for main summary panels

        # Logo and Store Name (Top Left)
        logo_frame = ttk.Frame(self.dashboard_frame)
        logo_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nw")
        
        if self.logo_image:
            logo_label = ttk.Label(logo_frame, image=self.logo_image)
            logo_label.pack(side="left", padx=5, pady=5)
        
        # Add store name text (Beng's Sari-Sari Store)
        # Changed font for 'Beng's Sari-Sari Store'
        store_name_label = ttk.Label(logo_frame, text="Beng's\nSari-Sari Store", font=("Verdana", 14, "bold"))
        store_name_label.pack(side="left", padx=5, pady=5)


        # Date and Time Display (Top Right within the right column)
        datetime_frame = ttk.Frame(self.dashboard_frame)
        datetime_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ne") # Placed top-right
        ttk.Label(datetime_frame, text="Date :").grid(row=0, column=0, sticky="w", padx=2, pady=1)
        self.date_lbl = ttk.Label(datetime_frame, text="TODAY()")
        self.date_lbl.grid(row=0, column=1, sticky="w", padx=2, pady=1)
        ttk.Label(datetime_frame, text="Time :").grid(row=1, column=0, sticky="w", padx=2, pady=1)
        self.time_lbl = ttk.Label(datetime_frame, text="(12hr with secs)")
        self.time_lbl.grid(row=1, column=1, sticky="w", padx=2, pady=1)
        
        # Key Metrics Panel (Left Side, below logo and store name)
        key_metrics_panel = ttk.LabelFrame(self.dashboard_frame, text="Key Metrics", padding="15")
        key_metrics_panel.grid(row=1, column=0, sticky="nsew", padx=10, pady=10) # Placed in row 1, column 0
        key_metrics_panel.columnconfigure(1, weight=1) # Column for values to expand
        key_metrics_panel.columnconfigure(3, weight=1) # Column for second set of values to expand

        # Row 0
        ttk.Label(key_metrics_panel, text="Inventory Value :").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.selling_inv_value_lbl = ttk.Label(key_metrics_panel, text="₱0.00")
        self.selling_inv_value_lbl.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(key_metrics_panel, text="Items Sold :").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.items_sold_cogs_lbl = ttk.Label(key_metrics_panel, text="(COGS)")
        self.items_sold_cogs_lbl.grid(row=0, column=3, padx=5, pady=2, sticky="w")

        # Row 1
        ttk.Label(key_metrics_panel, text="Supplier Value :").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.supplier_inv_value_lbl = ttk.Label(key_metrics_panel, text="₱0.00")
        self.supplier_inv_value_lbl.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(key_metrics_panel, text="Supplier (Per Unit) :").grid(row=1, column=2, padx=5, pady=2, sticky="w")
        self.supplier_per_unit_cogs_lbl = ttk.Label(key_metrics_panel, text="(Supplier Price (Per Unit) * quantity_sold)")
        self.supplier_per_unit_cogs_lbl.grid(row=1, column=3, padx=5, pady=2, sticky="w")

        # Row 2
        ttk.Label(key_metrics_panel, text="Projected Profit :").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.projected_profit_lbl = ttk.Label(key_metrics_panel, text="₱0.00", foreground="purple")
        self.projected_profit_lbl.grid(row=2, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(key_metrics_panel, text="Profit :").grid(row=2, column=2, padx=5, pady=2, sticky="w")
        self.gross_profit_from_sold_items_lbl = ttk.Label(key_metrics_panel, text="(Items Sold - Supplier (Per Unit))", foreground="green")
        self.gross_profit_from_sold_items_lbl.grid(row=2, column=3, padx=5, pady=2, sticky="w")

        # Row 3
        ttk.Label(key_metrics_panel, text="Re-Order Cost :").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.reorder_cost_lbl = ttk.Label(key_metrics_panel, text="₱0.00")
        self.reorder_cost_lbl.grid(row=3, column=1, padx=5, pady=2, sticky="w")


        # Sales Statistics Panel (Right Side, below Date/Time)
        sales_stats_panel = ttk.LabelFrame(self.dashboard_frame, text="Sales Statistics", padding="15")
        sales_stats_panel.grid(row=1, column=1, sticky="nsew", padx=10, pady=10) # Placed in row 1, column 1
        sales_stats_panel.columnconfigure(0, weight=1) # Column for "Collected" values
        sales_stats_panel.columnconfigure(1, weight=1) # Column for "Profit" values

        # Sales Count
        ttk.Label(sales_stats_panel, text="Sales Count :").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.sales_count_lbl = ttk.Label(sales_stats_panel, text="0")
        self.sales_count_lbl.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        # Collected / Profit Headers - Aligned to the right
        ttk.Label(sales_stats_panel, text="Collected", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(sales_stats_panel, text="Profit", font=("Arial", 10, "bold")).grid(row=1, column=1, padx=5, pady=5, sticky="e")

        # Daily
        ttk.Label(sales_stats_panel, text="Daily :").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.daily_sales_lbl = ttk.Label(sales_stats_panel, text="₱0.00")
        self.daily_sales_lbl.grid(row=2, column=0, padx=5, pady=2, sticky="e") # Collected value
        self.daily_profit_lbl = ttk.Label(sales_stats_panel, text="₱0.00")
        self.daily_profit_lbl.grid(row=2, column=1, padx=5, pady=2, sticky="e") # Profit value

        # Weekly
        ttk.Label(sales_stats_panel, text="Weekly :").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.weekly_sales_lbl = ttk.Label(sales_stats_panel, text="₱0.00")
        self.weekly_sales_lbl.grid(row=3, column=0, padx=5, pady=2, sticky="e")
        self.weekly_profit_lbl = ttk.Label(sales_stats_panel, text="₱0.00")
        self.weekly_profit_lbl.grid(row=3, column=1, padx=5, pady=2, sticky="e")

        # Monthly
        ttk.Label(sales_stats_panel, text="Monthly :").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        self.monthly_sales_lbl = ttk.Label(sales_stats_panel, text="₱0.00")
        self.monthly_sales_lbl.grid(row=4, column=0, padx=5, pady=2, sticky="e")
        self.monthly_profit_lbl = ttk.Label(sales_stats_panel, text="₱0.00")
        self.monthly_profit_lbl.grid(row=4, column=1, padx=5, pady=2, sticky="e")

    def _initial_dashboard_refresh(self):
        """Performs the first refresh of the dashboard once the app is fully ready."""
        self.refresh_dashboard()
        # Initial refresh for POS search results, so the treeview is populated on startup
        self.pos_search_items() 


    def refresh_dashboard(self):
        """Refreshes the data displayed on the dashboard."""
        # Update Date and Time
        current_date = datetime.now().strftime('%d-%b-%Y')
        current_time = datetime.now().strftime('%I:%M:%S %p') # 12-hour format with AM/PM and seconds
        self.date_lbl.config(text=current_date)
        self.time_lbl.config(text=current_time)
        
        # Key Metrics calculations
        selling_inv_value = self.db.get_selling_inventory_value()
        supplier_inv_value = self.db.get_supplier_inventory_value()
        projected_profit_inventory = selling_inv_value - supplier_inv_value

        self.selling_inv_value_lbl.config(text=f"₱{selling_inv_value:.2f}")
        self.supplier_inv_value_lbl.config(text=f"₱{supplier_inv_value:.2f}")
        self.projected_profit_lbl.config(text=f"₱{projected_profit_inventory:.2f}")
        
        # Update color for projected profit
        if projected_profit_inventory < 0:
            self.projected_profit_lbl.config(foreground="red")
        else:
            self.projected_profit_lbl.config(foreground="green") # Keep green if positive or zero


        reorder_cost = self.db.get_reorder_cost()
        self.reorder_cost_lbl.config(text=f"₱{reorder_cost:.2f}")

        # Sales Count (Today)
        today_date_str = datetime.now().strftime('%Y-%m-%d')
        start_of_day = f"{today_date_str} 00:00:00"
        end_of_day = f"{today_date_str} 23:59:59"
        
        self.db.cursor.execute("SELECT COUNT(*) FROM sales WHERE sale_date BETWEEN ? AND ?", (start_of_day, end_of_day))
        sales_count_today = self.db.cursor.fetchone()[0] or 0
        self.sales_count_lbl.config(text=f"{sales_count_today}")

        # Get sales summary for Key Metrics specific profit calculation
        _, cogs_selling_price_based_today, cogs_supplier_price_based_today = self.db.get_sales_summary(start_of_day, end_of_day)

        self.items_sold_cogs_lbl.config(text=f"₱{cogs_selling_price_based_today:.2f}")
        self.supplier_per_unit_cogs_lbl.config(text=f"₱{cogs_supplier_price_based_today:.2f}")
        
        # Profit for "Items Sold - Supplier (Per Unit)"
        gross_profit_from_sold_items = cogs_selling_price_based_today - cogs_supplier_price_based_today
        self.gross_profit_from_sold_items_lbl.config(text=f"₱{gross_profit_from_sold_items:.2f}")
        if gross_profit_from_sold_items < 0:
            self.gross_profit_from_sold_items_lbl.config(foreground="red")
        else:
            self.gross_profit_from_sold_items_lbl.config(foreground="green")


        # Update sales and profit statistics (Daily, Weekly, Monthly from Profit & Expenses tab)
        self.refresh_profit_summary() # This will update the daily/weekly/monthly labels for Sales and Profit

    # --- Inventory Management Tab ---
    def create_inventory_tab(self):
        self.inventory_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.inventory_frame, text="Inventory Management")
        self.inventory_frame.columnconfigure(0, weight=1)
        self.inventory_frame.rowconfigure(1, weight=1) # Row for Treeview

        # Search and Action buttons
        control_frame = ttk.Frame(self.inventory_frame, padding="10")
        control_frame.grid(row=0, column=0, sticky="ew", pady=5)
        control_frame.columnconfigure(1, weight=1)

        ttk.Label(control_frame, text="Search Item:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.inventory_search_entry = ttk.Entry(control_frame, width=40)
        self.inventory_search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.inventory_search_entry.bind("<KeyRelease>", self.search_inventory_items) # Live search

        ttk.Button(control_frame, text="Add Item", command=self.open_add_edit_item_window).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(control_frame, text="Edit Item", command=self.edit_selected_inventory_item).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(control_frame, text="Delete Item", command=self.delete_selected_inventory_item).grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(control_frame, text="Export CSV", command=lambda: self.export_inventory("csv")).grid(row=0, column=5, padx=5, pady=5)
        ttk.Button(control_frame, text="Export JSON", command=lambda: self.export_inventory("json")).grid(row=0, column=6, padx=5, pady=5)
        ttk.Button(control_frame, text="Import", command=self.import_inventory).grid(row=0, column=7, padx=5, pady=5)


        # Inventory Treeview - Updated column heading
        self.inventory_tree = ttk.Treeview(self.inventory_frame, columns=(
            'Item No.', 'Item Name', 'Description', 'Unit', 'Supplier Price (Per Unit)', 'Sell. Price', 'Stock', 'Re-Order', 'Re-Order QTY'
        ), show='headings')
        self.inventory_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Define column headings and widths - Updated column heading
        cols = ['Item No.', 'Item Name', 'Description', 'Unit', 'Supplier Price (Per Unit)', 'Sell. Price', 'Stock', 'Re-Order', 'Re-Order QTY']
        widths = [80, 150, 200, 70, 120, 90, 70, 80, 100] # Adjusted width for new column title
        
        # Mapping column names to internal identifiers for sorting
        self.inventory_column_map = {
            'Item No.': 'item_no',
            'Item Name': 'item_name',
            'Description': 'item_description',
            'Unit': 'unit',
            'Supplier Price (Per Unit)': 'supplier_price_per_unit_display', # Internal key for derived value
            'Sell. Price': 'selling_price',
            'Stock': 'current_stock',
            'Re-Order': 'reorder_status',
            'Re-Order QTY': 'reorder_qty_display',
        }
        
        # Store current sorting column and order
        self.inventory_sort_column = None
        self.inventory_sort_reverse = False

        for col, width in zip(cols, widths):
            self.inventory_tree.heading(col, text=col, command=lambda c=col: self._sort_inventory_treeview_column(c))
            self.inventory_tree.column(col, width=width, anchor="center")
        
        # Set specific alignments for 'Item Name' and 'Description'
        self.inventory_tree.column('Item Name', anchor="w") # Left align Item Name
        self.inventory_tree.column('Description', anchor="w") # Left align Description
        self.inventory_tree.column('Supplier Price (Per Unit)', anchor="e") # Right align price
        self.inventory_tree.column('Sell. Price', anchor="e") # Right align price

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.inventory_frame, orient="vertical", command=self.inventory_tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=10)
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)

        self.refresh_inventory_list()

    def _sort_inventory_treeview_column(self, col_name):
        """Sorts the inventory treeview by the given column."""
        # Determine internal data key for the column
        data_key = self.inventory_column_map.get(col_name)
        if not data_key:
            return # Should not happen if mapping is correct

        # Get all items from the treeview
        items = [(self.inventory_tree.set(k, col_name), k) for k in self.inventory_tree.get_children('')]

        # Toggle sort order if clicking the same column
        if self.inventory_sort_column == col_name:
            self.inventory_sort_reverse = not self.inventory_sort_reverse
        else:
            self.inventory_sort_column = col_name
            self.inventory_sort_reverse = False # Default to ascending for new column

        # Custom sorting logic based on column type
        if data_key in ['supplier_price_per_unit_display', 'selling_price']: # Use the new internal key
            # Convert currency string "₱123.45" to float 123.45
            items.sort(key=lambda t: float(t[0].replace('₱', '')), reverse=self.inventory_sort_reverse)
        elif data_key in ['current_stock', 'reorder_level', 'reorder_qty_display']:
            # Convert to int for numerical sorting
            items.sort(key=lambda t: int(t[0]) if t[0] != '' else 0, reverse=self.inventory_sort_reverse)
        elif data_key == 'reorder_status':
            # Sort 'Yes' before 'No' for ascending, 'No' before 'Yes' for descending
            items.sort(key=lambda t: 0 if t[0] == 'Yes' else 1, reverse=self.inventory_sort_reverse)
        else:
            # Default string sorting
            items.sort(key=lambda t: t[0].lower(), reverse=self.inventory_sort_reverse)

        # Rearrange items in treeview
        for index, (val, k) in enumerate(items):
            self.inventory_tree.move(k, '', index)

    def refresh_inventory_list(self, items=None):
        """Clears and repopulates the inventory treeview."""
        for i in self.inventory_tree.get_children():
            self.inventory_tree.delete(i)
        if items == None: # Corrected from === to ==
            items = self.db.get_all_items()

        for item in items:
            # UNPACKING CHANGE: Account for 'volume' and 'interest' columns
            # This line still needs to unpack all 11 values from the database query
            item_no, item_name, desc, unit, supplier_price_investment, sell_price, stock, reorder_lvl, reorder_qty, volume, interest = item
            
            # Ensure numerical values are not None before formatting
            supplier_price_investment = float(supplier_price_investment) if supplier_price_investment is not None else 0.0
            sell_price = float(sell_price) if sell_price is not None else 0.0
            volume = int(volume) if volume is not None else 1 # Ensure volume is an integer for calculation
            volume = max(1, volume) # Prevent division by zero

            supplier_price_per_unit = supplier_price_investment / volume # Calculate per unit price

            reorder_status = "Yes" if stock < reorder_lvl else "No"
            # Calculate suggested re-order quantity if below level
            suggested_reorder = max(0, reorder_lvl - stock) if stock < reorder_lvl else 0
            # If reorder_qty is specifically set for an item and it's flagged, use that, otherwise use calculated
            actual_reorder_qty_display = reorder_qty if reorder_status == "Yes" and reorder_qty > 0 else suggested_reorder

            # Insert into Treeview - Use calculated supplier_price_per_unit
            self.inventory_tree.insert("", "end", values=(
                item_no, item_name, desc, unit, f"₱{supplier_price_per_unit:.2f}", f"₱{sell_price:.2f}",
                stock, reorder_status, actual_reorder_qty_display
            ), tags=('reorder' if reorder_status == "Yes" else ''))

        self.inventory_tree.tag_configure('reorder', background='#FFDDDD') # Light red background for reorder items

    def search_inventory_items(self, event=None):
        """Searches inventory items based on the entry field."""
        query = self.inventory_search_entry.get().strip()
        if query:
            items = self.db.get_item_by_no_or_name(query)
        else:
            items = self.db.get_all_items()
        self.refresh_inventory_list(items)

    def open_add_edit_item_window(self, item_data=None):
        """Opens a new window for adding or editing inventory items."""
        # Added 'Interest' to the labels list for the input form
        labels = ['Item No.', 'Item Name', 'Description', 'Unit', 'Supplier Price', 'Selling Price', 'Current Stock', 'Re-Order Level', 'Re-Order QTY', 'Volume', 'Interest']
        
        window = tk.Toplevel(self)
        window.title("Add/Edit Inventory Item")
        window.geometry("400x400") # Increased height to accommodate new field
        window.transient(self) # Make it modal

        entries = {}

        for i, text in enumerate(labels):
            ttk.Label(window, text=text + ":").grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = ttk.Entry(window, width=40)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entries[text] = entry

        # Populate for edit mode
        if item_data:
            window.title("Edit Inventory Item")
            # Clear and insert for each entry to prevent TclError
            # Item data now contains 11 elements including volume and interest
            entries['Item No.'].delete(0, tk.END)
            entries['Item No.'].insert(0, str(item_data[0]) if item_data[0] is not None else '')
            entries['Item No.']['state'] = 'readonly' # Item No cannot be changed

            entries['Item Name'].delete(0, tk.END)
            entries['Item Name'].insert(0, str(item_data[1]) if item_data[1] is not None else '')

            entries['Description'].delete(0, tk.END)
            entries['Description'].insert(0, str(item_data[2]) if item_data[2] is not None else '')

            entries['Unit'].delete(0, tk.END)
            entries['Unit'].insert(0, str(item_data[3]) if item_data[3] is not None else '')

            # supplier_price (item_data[4]) is the Investment price in the database
            entries['Supplier Price'].delete(0, tk.END)
            entries['Supplier Price'].insert(0, str(item_data[4]) if item_data[4] is not None else '')

            entries['Selling Price'].delete(0, tk.END)
            entries['Selling Price'].insert(0, str(item_data[5]) if item_data[5] is not None else '')

            entries['Current Stock'].delete(0, tk.END)
            entries['Current Stock'].insert(0, str(item_data[6]) if item_data[6] is not None else '')

            entries['Re-Order Level'].delete(0, tk.END)
            entries['Re-Order Level'].insert(0, str(item_data[7]) if item_data[7] is not None else '')

            entries['Re-Order QTY'].delete(0, tk.END)
            entries['Re-Order QTY'].insert(0, str(item_data[8]) if item_data[8] is not None else '')
            
            entries['Volume'].delete(0, tk.END)
            entries['Volume'].insert(0, str(item_data[9]) if item_data[9] is not None else '1') # Populate volume

            entries['Interest'].delete(0, tk.END)
            entries['Interest'].insert(0, str(item_data[10]) if item_data[10] is not None else '0') # Populate interest

            # Profit calculation helper for 'Selling Price'
            entries['Supplier Price'].bind("<FocusOut>", lambda e: self.calculate_selling_price_suggestion(entries))
            entries['Supplier Price'].bind("<Return>", lambda e: self.calculate_selling_price_suggestion(entries))

        def save_item():
            item_no = entries['Item No.'].get().strip()
            item_name = entries['Item Name'].get().strip()
            item_description = entries['Description'].get().strip()
            unit = entries['Unit'].get().strip()

            try:
                # This 'Supplier Price' field is for the Investment Price
                supplier_price = float(entries['Supplier Price'].get())
                selling_price = float(entries['Selling Price'].get())
                current_stock = int(entries['Current Stock'].get())
                reorder_level = int(entries['Re-Order Level'].get() or 5)
                reorder_qty = int(entries['Re-Order QTY'].get() or 0)
                volume = int(entries['Volume'].get() or 1) # Get volume, default to 1
                if volume <= 0:
                    messagebox.showerror("Input Error", "Volume must be a positive number (at least 1).")
                    return
                interest = int(entries['Interest'].get() or 0) # Get interest, default to 0
            except ValueError:
                messagebox.showerror("Input Error", "Please enter valid numbers for prices, stock, re-order quantities, volume, and interest.")
                return

            if not item_no or not item_name:
                messagebox.showerror("Input Error", "Item No. and Item Name are required.")
                return

            data = {
                'item_no': item_no,
                'item_name': item_name,
                'item_description': item_description,
                'unit': unit,
                'supplier_price': supplier_price, # This is the 'Supplier Price (Investment)'
                'selling_price': selling_price,
                'current_stock': current_stock,
                'reorder_level': reorder_level,
                'reorder_qty': reorder_qty,
                'volume': volume, # Include volume in data
                'interest': interest # Include interest in data
            }

            success = False
            if item_data: # Edit existing
                success = self.db.update_item(item_data[0], data)
            else: # Add new
                success = self.db.add_item(data)

            if success:
                messagebox.showinfo("Success", "Item saved successfully!")
                self.refresh_inventory_list()
                self.refresh_pricing_list() # Refresh pricing as well
                window.destroy()

        ttk.Button(window, text="Save", command=save_item).grid(row=len(labels), column=0, columnspan=2, pady=10)

    def calculate_selling_price_suggestion(self, entries):
        """Calculates and suggests a selling price based on supplier price (investment)."""
        try:
            # This is the Supplier Price (Investment)
            supplier_price_investment = float(entries['Supplier Price'].get())
            volume = int(entries['Volume'].get() or 1)
            volume = max(1, volume) # Ensure volume is at least 1

            supplier_price_per_unit = supplier_price_investment / volume
            interest = int(entries['Interest'].get() or 0)
            
            suggested_selling_price = supplier_price_per_unit + interest
            
            # Suggest selling price, round up
            suggested_selling_price_rounded = math.ceil(suggested_selling_price)

            # Only suggest if the current field is empty or lower than the suggestion
            current_selling_price_text = entries['Selling Price'].get().strip()
            if not current_selling_price_text or float(current_selling_price_text) < suggested_selling_price_rounded:
                entries['Selling Price'].delete(0, tk.END)
                entries['Selling Price'].insert(0, f"{suggested_selling_price_rounded:.2f}")
        except ValueError:
            pass # Ignore if inputs are not valid numbers


    def edit_selected_inventory_item(self):
        """Opens the add/edit window pre-filled with selected item's data."""
        selected_item = self.inventory_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select an item to edit.")
            return
        item_no = self.inventory_tree.item(selected_item[0])['values'][0]
        item_data = self.db.get_item_by_item_no(item_no)
        if item_data:
            self.open_add_edit_item_window(item_data)

    def delete_selected_inventory_item(self):
        """Deletes the selected inventory item."""
        selected_item = self.inventory_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select an item to delete.")
            return
        item_no = self.inventory_tree.item(selected_item[0])['values'][0]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete item '{item_no}'?"):
            if self.db.delete_item(item_no):
                messagebox.showinfo("Success", "Item deleted successfully!")
                self.refresh_inventory_list()
                self.refresh_pricing_list() # Refresh pricing as well
            else:
                messagebox.showerror("Error", "Failed to delete item.")

    def export_inventory(self, file_type):
        """Exports inventory data to CSV or JSON."""
        items = self.db.get_all_items()
        if not items:
            messagebox.showinfo("Export", "No data to export.")
            return

        df = pd.DataFrame(items, columns=[
            'Item No.', 'Item Name', 'Item Description', 'Unit', 'Supplier Price (Investment)', 'Selling Price', # Renamed column to match database
            'Current Stock', 'Re-Order Level', 'Re-Order QTY', 'Volume', 'Interest' # Added 'Volume' and 'Interest'
        ])

        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{file_type}",
            filetypes=[(f"{file_type.upper()} files", f"*.{file_type}"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            if file_type == "csv":
                df.to_csv(file_path, index=False)
            elif file_type == "json":
                df.to_json(file_path, orient="records", indent=4)
            messagebox.showinfo("Export Success", f"Inventory exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {e}")

    def import_inventory(self):
        """Imports inventory data from CSV or JSON."""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return

        # Helper function to parse currency strings to float
        def parse_currency(value):
            if pd.isna(value):
                return 0.0
            s_value = str(value).strip()
            # Remove currency symbols and comma separators
            s_value = s_value.replace('₱', '').replace('P', '').replace('$', '').replace(',', '')
            try:
                return float(s_value)
            except ValueError:
                return 0.0 # Default to 0.0 if conversion fails

        # Helper function to parse integer values
        def parse_int(value, default=0):
            if pd.isna(value):
                return default
            s_value = str(value).strip()
            # Remove any non-numeric characters that might sneak in (e.g., from badly formatted numbers)
            s_value = ''.join(filter(str.isdigit, s_value))
            try:
                return int(s_value)
            except ValueError:
                return default # Default if conversion fails

        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.json'):
                df = pd.read_json(file_path)
            else:
                messagebox.showerror("Import Error", "Unsupported file type. Please select a CSV or JSON file.")
                return

            # Validate columns - ensure required_cols are present
            # CRITICAL FIX: Changed 'Supplier Price' to 'Supplier Price (Investment)'
            required_cols = ['Item No.', 'Item Name', 'Supplier Price (Investment)', 'Selling Price', 'Current Stock']
            if not all(col in df.columns for col in required_cols):
                messagebox.showerror("Import Error", f"Missing required columns. Ensure file has: {', '.join(required_cols)}")
                return

            imported_count = 0
            updated_count = 0
            for index, row in df.iterrows():
                # Safely retrieve string values, defaulting to empty string if missing or NaN
                item_no = str(row.get('Item No.', '')) if pd.notna(row.get('Item No.')) else ''
                item_name = str(row.get('Item Name', '')) if pd.notna(row.get('Item Name')) else ''
                item_description = str(row.get('Item Description', '')) if pd.notna(row.get('Item Description')) else ''
                unit = str(row.get('Unit', '')) if pd.notna(row.get('Unit')) else ''

                # Use helper functions for robust parsing
                # CRITICAL FIX: Get 'Supplier Price (Investment)' from CSV
                supplier_price = parse_currency(row.get('Supplier Price (Investment)', 0.0))
                selling_price = parse_currency(row.get('Selling Price', 0.0))
                current_stock = parse_int(row.get('Current Stock', 0), 0)
                reorder_level = parse_int(row.get('Re-Order Level', 5), 5)
                reorder_qty = parse_int(row.get('Re-Order QTY', 0), 0)
                
                volume = parse_int(row.get('Volume', 1), 1) # Get volume, default to 1 if missing
                if volume <= 0:
                    messagebox.showwarning("Import Warning", f"Volume for item '{item_no}' was invalid ({volume}). Setting to 1.")
                    volume = 1
                
                interest = parse_int(row.get('Interest', 0), 0) # Get interest, default to 0 if missing


                data = {
                    'item_no': item_no,
                    'item_name': item_name,
                    'item_description': item_description,
                    'unit': unit,
                    'supplier_price': supplier_price, # This is the 'Supplier Price (Investment)' from the CSV
                    'selling_price': selling_price,
                    'current_stock': current_stock,
                    'reorder_level': reorder_level,
                    'reorder_qty': reorder_qty,
                    'volume': volume, # Include volume in data
                    'interest': interest # Include interest in data
                }

                existing_item = self.db.get_item_by_item_no(data['item_no'])
                if existing_item:
                    # Update existing item
                    if self.db.update_item(data['item_no'], data):
                        updated_count += 1
                else:
                    # Add new item
                    if self.db.add_item(data):
                        imported_count += 1

            messagebox.showinfo("Import Success", f"Import complete. Added: {imported_count}, Updated: {updated_count} items.")
            self.refresh_inventory_list()
            self.refresh_pricing_list()

        except KeyError as ke:
            messagebox.showerror("Import Error", f"Missing expected column in CSV/JSON: {ke}. Please ensure the file has the correct headers.")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import data: {e}")

    # --- POS Tab ---
    def create_pos_tab(self):
        self.pos_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.pos_frame, text="POS")

        # Configure pos_frame to have two main columns
        self.pos_frame.columnconfigure(0, weight=1) # Left column (search and cart) will expand
        self.pos_frame.columnconfigure(1, weight=0, minsize=350) # Right column (billing) will take minimum space, then we'll manage its width
        self.pos_frame.rowconfigure(0, weight=1) # The single row will expand vertically

        # --- Left Content Frame (for Search Item and Shopping Cart) ---
        left_content_frame = ttk.Frame(self.pos_frame)
        left_content_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        left_content_frame.columnconfigure(0, weight=1) # Inner column expands
        left_content_frame.rowconfigure(0, weight=0) # Search panel row - fixed height
        left_content_frame.rowconfigure(1, weight=1) # Cart panel row - expands vertically

        # Item Search Panel (inside left_content_frame)
        search_panel = ttk.LabelFrame(left_content_frame, text="Search Item", padding="10")
        search_panel.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        search_panel.columnconfigure(0, weight=0) # Item No./Name label
        search_panel.columnconfigure(1, weight=1) # Item No./Name entry
        search_panel.columnconfigure(2, weight=0) # Quantity label
        search_panel.columnconfigure(3, weight=0) # Quantity entry
        search_panel.columnconfigure(4, weight=0) # Add to Cart button

        ttk.Label(search_panel, text="Item No./Name:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.pos_search_entry = ttk.Entry(search_panel, width=50)
        self.pos_search_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew", columnspan=4) # Span across available columns
        self.pos_search_entry.bind("<KeyRelease>", self.pos_search_items)

        # Replaced Listbox with Treeview for search results
        self.pos_results_tree = ttk.Treeview(search_panel, columns=(
            'Item No.', 'Item Name', 'Description', 'Unit', 'Stock', 'Selling Price'
        ), show='headings', height=5) # Increased height for more visible results
        self.pos_results_tree.grid(row=1, column=0, columnspan=5, padx=5, pady=2, sticky="nsew")

        # Define column headings and widths for search results treeview
        self.pos_results_tree.heading('Item No.', text='Item No.')
        self.pos_results_tree.column('Item No.', width=80, anchor="center")
        self.pos_results_tree.heading('Item Name', text='Item Name')
        self.pos_results_tree.column('Item Name', width=150, anchor="w")
        self.pos_results_tree.heading('Description', text='Description')
        self.pos_results_tree.column('Description', width=150, anchor="w")
        self.pos_results_tree.heading('Unit', text='Unit')
        self.pos_results_tree.column('Unit', width=70, anchor="center")
        self.pos_results_tree.heading('Stock', text='Stock')
        self.pos_results_tree.column('Stock', width=70, anchor="center")
        self.pos_results_tree.heading('Selling Price', text='Selling Price')
        self.pos_results_tree.column('Selling Price', width=90, anchor="e") # Align price to right

        # Scrollbar for search results treeview
        search_results_scrollbar = ttk.Scrollbar(search_panel, orient="vertical", command=self.pos_results_tree.yview)
        search_results_scrollbar.grid(row=1, column=5, sticky="ns", pady=2)
        self.pos_results_tree.configure(yscrollcommand=search_results_scrollbar.set)
        
        # Bind selection event for the new Treeview
        self.pos_results_tree.bind("<<TreeviewSelect>>", self.pos_select_item)

        ttk.Label(search_panel, text="Quantity:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.pos_qty_entry = ttk.Entry(search_panel, width=10)
        self.pos_qty_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")
        self.pos_qty_entry.insert(0, "1")

        ttk.Button(search_panel, text="Add to Cart", command=self.add_item_to_cart).grid(row=2, column=4, padx=5, pady=2, sticky="e") # Adjusted column for button

        # Shopping Cart Panel (inside left_content_frame)
        cart_panel = ttk.LabelFrame(left_content_frame, text="Shopping Cart", padding="10")
        cart_panel.grid(row=1, column=0, sticky="nsew", padx=5, pady=5) # This should expand
        cart_panel.columnconfigure(0, weight=1)
        cart_panel.rowconfigure(0, weight=1) # Treeview inside cart panel expands

        self.pos_cart_tree = ttk.Treeview(cart_panel, columns=(
            'Item No.', 'Item Name', 'Quantity', 'Price', 'Subtotal'
        ), show='headings')
        # Further reduced height for the shopping cart treeview to make space for billing
        self.pos_cart_tree.config(height=6) # Set explicit height
        self.pos_cart_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=2)

        for col in ['Item No.', 'Item Name', 'Quantity', 'Price', 'Subtotal']:
            self.pos_cart_tree.heading(col, text=col)
            self.pos_cart_tree.column(col, width=100, anchor="center")
        self.pos_cart_tree.column('Item Name', width=180)

        cart_scrollbar = ttk.Scrollbar(cart_panel, orient="vertical", command=self.pos_cart_tree.yview)
        cart_scrollbar.grid(row=0, column=1, sticky="ns", pady=2)
        self.pos_cart_tree.configure(yscrollcommand=cart_scrollbar.set)

        ttk.Button(cart_panel, text="Remove Selected", command=self.remove_item_from_cart).grid(row=1, column=0, pady=5, sticky="e")

        # --- Billing Summary and Payment Panel (Right Column) ---
        billing_panel = ttk.LabelFrame(self.pos_frame, text="Billing & Payment", padding="10")
        billing_panel.grid(row=0, column=1, sticky="ns", padx=5, pady=5) # Placed in right column, sticks North-South
        billing_panel.columnconfigure(1, weight=1) # Make column 1 expand within billing_panel

        # Adjusted row weights and pady for a more compact layout
        billing_panel.rowconfigure(0, weight=0) # Total Amount - fixed height
        billing_panel.rowconfigure(1, weight=0) # Payment Type - fixed height
        billing_panel.rowconfigure(2, weight=0) # Amount Paid - fixed height
        billing_panel.rowconfigure(3, weight=0) # Additional Charge
        billing_panel.rowconfigure(4, weight=0) # Change
        billing_panel.rowconfigure(5, weight=0) # Customer Name (NEW POSITION)
        billing_panel.rowconfigure(6, weight=0) # Process Sale button (NEW POSITION)

        ttk.Label(billing_panel, text="Total Amount:").grid(row=0, column=0, padx=5, pady=1, sticky="w")
        self.pos_total_amount_lbl = ttk.Label(billing_panel, text="₱0.00", font=("Arial", 16, "bold"))
        self.pos_total_amount_lbl.grid(row=0, column=1, padx=5, pady=1, sticky="e")

        ttk.Label(billing_panel, text="Payment Type:").grid(row=1, column=0, padx=5, pady=1, sticky="w")
        
        # Frame for radio buttons for better packing
        radio_button_frame = ttk.Frame(billing_panel)
        radio_button_frame.grid(row=1, column=1, padx=5, pady=1, sticky="w")

        self.payment_type_var = tk.StringVar(value="Cash")
        cash_radio = ttk.Radiobutton(radio_button_frame, text="Cash", variable=self.payment_type_var, value="Cash", command=self.toggle_credit_fields)
        cash_radio.pack(side="left", padx=5) # Use pack for horizontal arrangement within the frame
        credit_radio = ttk.Radiobutton(radio_button_frame, text="Credit", variable=self.payment_type_var, value="Credit", command=self.toggle_credit_fields)
        credit_radio.pack(side="left", padx=5) # Use pack for horizontal arrangement within the frame

        ttk.Label(billing_panel, text="Amount Paid:").grid(row=2, column=0, padx=5, pady=1, sticky="w")
        self.paid_amount_entry = ttk.Entry(billing_panel, width=30)
        self.paid_amount_entry.grid(row=2, column=1, padx=5, pady=1, sticky="ew")
        self.paid_amount_entry.bind("<KeyRelease>", self.calculate_change) # Bind for dynamic change calculation

        ttk.Label(billing_panel, text="Additional Charge:").grid(row=3, column=0, padx=5, pady=1, sticky="w")
        self.pos_additional_charge_entry = ttk.Entry(billing_panel, width=30)
        self.pos_additional_charge_entry.grid(row=3, column=1, padx=5, pady=1, sticky="ew")
        self.pos_additional_charge_entry.insert(0, "0.00") # Default to 0
        self.pos_additional_charge_entry.bind("<KeyRelease>", self.calculate_change) # Bind for dynamic change calculation

        ttk.Label(billing_panel, text="Change:").grid(row=4, column=0, padx=5, pady=1, sticky="w")
        self.pos_change_lbl = ttk.Label(billing_panel, text="₱0.00", font=("Arial", 14, "bold"), foreground="blue")
        self.pos_change_lbl.grid(row=4, column=1, padx=5, pady=1, sticky="e")

        # Customer Name fields - always present, state controlled by toggle_credit_fields
        self.customer_name_lbl = ttk.Label(billing_panel, text="Customer Name:")
        self.customer_name_lbl.grid(row=5, column=0, padx=5, pady=1, sticky="w") # New fixed row for customer name

        self.customer_name_entry = ttk.Entry(billing_panel, width=30)
        self.customer_name_entry.grid(row=5, column=1, padx=5, pady=1, sticky="ew") # New fixed row for customer name
        
        # The Process Sale button needs to be in its own row and can expand.
        ttk.Button(billing_panel, text="Process Sale", command=self.process_sale).grid(row=6, column=0, columnspan=2, pady=5, sticky="ew") # New fixed row for button

        # Add an empty row with weight=1 at the bottom to push all content to the top
        billing_panel.rowconfigure(7, weight=1) # Adjusted row for the flexible spacer


        self.pos_cart_items = [] # Stores dictionary of items in cart {item_no, name, qty, price, subtotal}
        self.update_pos_cart()
        self.toggle_credit_fields() # Call once at startup to set initial state


    def pos_search_items(self, event=None):
        """Searches for items in POS and updates the search results treeview."""
        query = self.pos_search_entry.get().strip()
        # Clear existing items in the treeview
        for i in self.pos_results_tree.get_children():
            self.pos_results_tree.delete(i)
        
        if query:
            items = self.db.get_item_by_no_or_name(query)
            for item in items:
                # item_no, item_name, desc, unit, sup_price_investment, sell_price, stock, reorder_lvl, reorder_qty, volume (index 9), interest (index 10)
                item_no, item_name, desc, unit, _, selling_price, current_stock, _, _, _, _ = item
                self.pos_results_tree.insert("", "end", values=(
                    item_no, item_name, desc, unit, current_stock, f"₱{selling_price:.2f}"
                ))
        self.selected_pos_item_data = None # Clear selected item data

    def pos_select_item(self, event=None):
        """Selects an item from the search results treeview and stores its data."""
        selected_item = self.pos_results_tree.selection()
        if selected_item:
            # Get the values from the selected row in the Treeview
            item_values = self.pos_results_tree.item(selected_item[0])['values']
            item_no = item_values[0] # Item No. is the first column
            self.selected_pos_item_data = self.db.get_item_by_item_no(item_no)

    def add_item_to_cart(self):
        """Adds the selected item to the POS cart."""
        if not self.selected_pos_item_data:
            messagebox.showwarning("No Item Selected", "Please search and select an item first.")
            return

        try:
            qty_to_add = int(self.pos_qty_entry.get())
            if qty_to_add <= 0:
                messagebox.showwarning("Invalid Quantity", "Quantity must be a positive number.")
                return
        except ValueError:
            messagebox.showwarning("Invalid Quantity", "Please enter a valid number for quantity.")
            return

        # Unpack all 11 fields, including volume and interest
        item_no, item_name, _, _, _, selling_price, current_stock, _, _, _, _ = self.selected_pos_item_data

        if qty_to_add > current_stock:
            messagebox.showwarning("Insufficient Stock", f"Only {current_stock} units of {item_name} are available.")
            return

        # Check if item already in cart, then update quantity
        found = False
        for item in self.pos_cart_items:
            if item['item_no'] == item_no:
                if item['quantity'] + qty_to_add > current_stock:
                    messagebox.showwarning("Insufficient Stock", f"Adding this quantity would exceed available stock for {item_name}.")
                    return
                item['quantity'] += qty_to_add
                item['subtotal'] = item['quantity'] * item['price_at_sale']
                found = True
                break
        if not found:
            self.pos_cart_items.append({
                'item_no': item_no,
                'item_name': item_name,
                'quantity': qty_to_add,
                'price_at_sale': selling_price,
                'subtotal': qty_to_add * selling_price
            })

        self.update_pos_cart()
        self.pos_search_entry.delete(0, tk.END) # Clear search after adding
        # Clear the search results treeview as well
        for i in self.pos_results_tree.get_children():
            self.pos_results_tree.delete(i)
        self.pos_qty_entry.delete(0, tk.END)
        self.pos_qty_entry.insert(0, "1")


    def remove_item_from_cart(self):
        """Removes selected item from POS cart."""
        selected_item = self.pos_cart_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select an item to remove from cart.")
            return

        # Get the item_no of the selected item from the Treeview
        item_no_to_remove = str(self.pos_cart_tree.item(selected_item[0])['values'][0]).strip()

        self.pos_cart_items = [item for item in self.pos_cart_items if str(item['item_no']).strip() != item_no_to_remove]
        
        # Refresh the display of the shopping cart (this already implicitly removes the item and its selection)
        self.update_pos_cart()
        
        # Removed the redundant selection_remove call which caused the TclError
        # self.pos_cart_tree.selection_remove(selected_item[0])


    def update_pos_cart(self):
        """Refreshes the POS cart treeview and total amount."""
        for i in self.pos_cart_tree.get_children():
            self.pos_cart_tree.delete(i)
        
        total_amount = 0.0
        for item in self.pos_cart_items:
            self.pos_cart_tree.insert("", "end", values=(
                item['item_no'], item['item_name'], item['quantity'],
                f"₱{item['price_at_sale']:.2f}", f"₱{item['subtotal']:.2f}"
            ))
            total_amount += item['subtotal']
        self.pos_total_amount_lbl.config(text=f"₱{total_amount:.2f}")
        self.calculate_change() # Recalculate change when cart updates


    def calculate_change(self, event=None):
        """Calculates and displays the change due."""
        try:
            cart_subtotal = sum(item['subtotal'] for item in self.pos_cart_items)
            
            additional_charge = float(self.pos_additional_charge_entry.get() or 0.0)
            if additional_charge < 0:
                messagebox.showwarning("Input Error", "Additional charge cannot be negative.")
                self.pos_additional_charge_entry.delete(0, tk.END)
                self.pos_additional_charge_entry.insert(0, "0.00")
                additional_charge = 0.0

            total_due = cart_subtotal + additional_charge

            # Update the total amount label to reflect additional charges
            self.pos_total_amount_lbl.config(text=f"₱{total_due:.2f}")

            paid_amount = float(self.paid_amount_entry.get() or 0.0)
            if paid_amount < 0:
                messagebox.showwarning("Input Error", "Amount paid cannot be negative.")
                self.paid_amount_entry.delete(0, tk.END)
                self.paid_amount_entry.insert(0, "0.00")
                paid_amount = 0.0

            change = paid_amount - total_due
            self.pos_change_lbl.config(text=f"₱{change:.2f}")

            if change < 0:
                self.pos_change_lbl.config(foreground="red")
            else:
                self.pos_change_lbl.config(foreground="blue")

        except ValueError:
            self.pos_change_lbl.config(text="Invalid Input", foreground="red")
            # Optionally clear the paid amount if it's invalid to prevent further errors
            # self.paid_amount_entry.delete(0, tk.END)
            # self.paid_amount_entry.insert(0, "0.00")


    def toggle_credit_fields(self):
        """Manages the state (enabled/disabled, content) of credit fields based on payment type."""
        # Amount Paid is always editable now for change calculation
        self.paid_amount_entry.config(state="normal")
        self.pos_additional_charge_entry.config(state="normal") # Additional charge always editable

        if self.payment_type_var.get() == "Credit":
            self.customer_name_entry.config(state="normal")
            self.customer_name_lbl.config(state="normal") # Ensure label is also normal

            # For credit, pre-fill paid amount with 0.0 and let user input, unless payment was already made
            # Set paid_amount to 0 to ensure proper calculation if no payment was made initially for a credit sale
            self.paid_amount_entry.delete(0, tk.END)
            self.paid_amount_entry.insert(0, "0.00")

        else: # Cash
            self.customer_name_entry.delete(0, tk.END)
            self.customer_name_entry.config(state="disabled")
            self.customer_name_lbl.config(state="disabled") # Disable label for consistency

            self.paid_amount_entry.delete(0, tk.END) # Clear paid amount for cash initially
            # No specific pre-fill for cash, user enters what they pay
        self.calculate_change() # Ensure change is calculated based on new state


    def process_sale(self):
        """Processes the sale, records it, and updates inventory."""
        if not self.pos_cart_items:
            messagebox.showwarning("Empty Cart", "No items in the cart to process sale.")
            return

        # Recalculate total amount including additional charge before processing
        try:
            cart_subtotal = sum(item['subtotal'] for item in self.pos_cart_items)
            additional_charge = float(self.pos_additional_charge_entry.get() or 0.0)
            total_amount_to_record = cart_subtotal + additional_charge
        except ValueError:
            messagebox.showwarning("Input Error", "Invalid value for additional charge.")
            return


        payment_type = self.payment_type_var.get()
        customer_name = ""
        paid_amount = 0.0
        status = "Paid"

        # Always try to get paid amount since it's always editable now
        try:
            paid_amount = float(self.paid_amount_entry.get() or 0.0)
        except ValueError:
            messagebox.showwarning("Input Error", "Please enter a valid number for Amount Paid.")
            return

        if payment_type == "Credit":
            customer_name = self.customer_name_entry.get().strip()
            if not customer_name:
                messagebox.showwarning("Input Error", "Customer Name is required for credit sales.")
                return

            if paid_amount < total_amount_to_record and paid_amount > 0:
                status = "Partially Paid"
            elif paid_amount == 0 and total_amount_to_record > 0: # Explicitly mark as Unpaid if 0 paid on a credit sale
                status = "Unpaid"
            elif paid_amount >= total_amount_to_record:
                status = "Paid"
        else: # Cash sale
            if paid_amount < total_amount_to_record:
                messagebox.showwarning("Insufficient Payment", "Amount paid is less than total amount due.")
                return
            status = "Paid" # Cash sales are assumed paid if amount is sufficient

        # Pass additional_charge to record_sale
        if self.db.record_sale(total_amount_to_record, payment_type, customer_name, paid_amount, status, additional_charge, self.pos_cart_items):
            messagebox.showinfo("Sale Processed", "Sale recorded successfully!")
            self.pos_cart_items.clear()
            self.update_pos_cart() # This will also trigger calculate_change

            # Reset POS fields
            self.pos_search_entry.delete(0, tk.END)
            for i in self.pos_results_tree.get_children(): # Clear search results treeview
                self.pos_results_tree.delete(i)
            self.pos_qty_entry.delete(0, tk.END)
            self.pos_qty_entry.insert(0, "1")
            self.customer_name_entry.delete(0, tk.END)
            self.paid_amount_entry.delete(0, tk.END)
            self.pos_additional_charge_entry.delete(0, tk.END)
            self.pos_additional_charge_entry.insert(0, "0.00")
            self.payment_type_var.set("Cash") # Reset to cash
            self.toggle_credit_fields() # Hide credit fields and re-initialize change
            self.refresh_inventory_list() # Update inventory view in case user switches tabs
            self.refresh_dashboard() # Refresh dashboard to update sales count
            self.refresh_sales_log() # Refresh sales log
        else:
            messagebox.showerror("Sale Error", "Failed to process sale.")

    # --- Stock In Log Tab ---
    def create_stock_in_tab(self):
        self.stock_in_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.stock_in_frame, text="Stock In Log")
        self.stock_in_frame.columnconfigure(0, weight=1)
        self.stock_in_frame.rowconfigure(1, weight=1)

        # Stock In Form
        form_frame = ttk.LabelFrame(self.stock_in_frame, text="Add New Stock In", padding="10")
        form_frame.grid(row=0, column=0, sticky="ew", pady=5)
        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(2, weight=1) # Allow search results to expand horizontally

        ttk.Label(form_frame, text="Item No./Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.stock_in_search_entry = ttk.Entry(form_frame, width=40)
        self.stock_in_search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew", columnspan=2) # Span across more columns
        self.stock_in_search_entry.bind("<KeyRelease>", self.stock_in_search_items)

        # Replaced Listbox with Treeview for stock in search results
        self.stock_in_results_tree = ttk.Treeview(form_frame, columns=(
            'Item No.', 'Item Name', 'Description', 'Unit', 'Stock', 'Selling Price'
        ), show='headings', height=5) # Increased height for more visible results
        self.stock_in_results_tree.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew") # Span across all columns

        # Define column headings and widths for search results treeview
        self.stock_in_results_tree.heading('Item No.', text='Item No.')
        self.stock_in_results_tree.column('Item No.', width=80, anchor="center")
        self.stock_in_results_tree.heading('Item Name', text='Item Name')
        self.stock_in_results_tree.column('Item Name', width=120, anchor="w")
        self.stock_in_results_tree.heading('Description', text='Description')
        self.stock_in_results_tree.column('Description', width=180, anchor="w")
        self.stock_in_results_tree.heading('Unit', text='Unit')
        self.stock_in_results_tree.column('Unit', width=70, anchor="center")
        self.stock_in_results_tree.heading('Stock', text='Stock')
        self.stock_in_results_tree.column('Stock', width=70, anchor="center")
        self.stock_in_results_tree.heading('Selling Price', text='Sell. Price')
        self.stock_in_results_tree.column('Selling Price', width=90, anchor="e")

        # Scrollbar for search results treeview
        stock_in_search_scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=self.stock_in_results_tree.yview)
        stock_in_search_scrollbar.grid(row=1, column=3, sticky="ns", pady=5) # Placed in the next column
        self.stock_in_results_tree.configure(yscrollcommand=stock_in_search_scrollbar.set)
        
        self.stock_in_results_tree.bind("<<TreeviewSelect>>", self.stock_in_select_item)


        ttk.Label(form_frame, text="Quantity Received:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.stock_in_qty_entry = ttk.Entry(form_frame, width=20)
        self.stock_in_qty_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew", columnspan=2) # Span across more columns

        ttk.Label(form_frame, text="Supplier:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.stock_in_supplier_entry = ttk.Entry(form_frame, width=40)
        self.stock_in_supplier_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew", columnspan=2) # Span across more columns

        # Removed Date Received field - it will now be set automatically
        # ttk.Label(form_frame, text="Date Received (YYYY-MM-DD):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        # self.stock_in_date_entry = ttk.Entry(form_frame, width=20)
        # self.stock_in_date_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew", columnspan=2)
        # self.stock_in_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d')) # Set default to current date


        ttk.Button(form_frame, text="Record Stock In", command=self.record_stock_in_entry).grid(row=4, column=0, columnspan=3, pady=10) # Adjusted row for button

        # Stock In Log Treeview (Main Log)
        self.stock_in_tree = ttk.Treeview(self.stock_in_frame, columns=(
            'Item No.', 'Item Name', 'Description', 'Quantity', 'Date Received', 'Supplier', 'Supplier Price'
        ), show='headings')
        self.stock_in_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Updated columns and widths for the main log treeview
        cols = ['Item No.', 'Item Name', 'Description', 'Quantity', 'Date Received', 'Supplier', 'Supplier Price']
        widths = [80, 150, 200, 80, 100, 120, 100] # Adjusted width for Date Received
        for col, width in zip(cols, widths):
            self.stock_in_tree.heading(col, text=col)
            self.stock_in_tree.column(col, width=width, anchor="center")
        self.stock_in_tree.column('Item Name', anchor="w")
        self.stock_in_tree.column('Description', anchor="w")


        scrollbar = ttk.Scrollbar(self.stock_in_frame, orient="vertical", command=self.stock_in_tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=10)
        self.stock_in_tree.configure(yscrollcommand=scrollbar.set)

        self.selected_stock_in_item_data = None
        self.refresh_stock_in_log()

    def stock_in_search_items(self, event=None):
        """Searches for items in Stock In tab and updates the search results treeview."""
        query = self.stock_in_search_entry.get().strip()
        # Clear existing items in the treeview
        for i in self.stock_in_results_tree.get_children():
            self.stock_in_results_tree.delete(i)
        
        if query:
            items = self.db.get_item_by_no_or_name(query)
            for item in items:
                # item_no, item_name, desc, unit, sup_price, sell_price, stock, reorder_lvl, reorder_qty, volume (index 9), interest (index 10)
                item_no, item_name, desc, unit, _, selling_price, current_stock, _, _, _, _ = item
                self.stock_in_results_tree.insert("", "end", values=(
                    item_no, item_name, desc, unit, current_stock, f"₱{selling_price:.2f}"
                ))
        self.selected_stock_in_item_data = None # Clear selected item data

    def stock_in_select_item(self, event=None):
        """Selects an item from the stock in search results."""
        selected_item = self.stock_in_results_tree.selection()
        if selected_item:
            # Get the values from the selected row in the Treeview
            item_values = self.stock_in_results_tree.item(selected_item[0])['values']
            item_no = item_values[0] # Item No. is the first column in the Treeview
            self.selected_stock_in_item_data = self.db.get_item_by_item_no(item_no)

    def record_stock_in_entry(self):
        """Records a new stock-in transaction."""
        if not self.selected_stock_in_item_data:
            messagebox.showwarning("No Item Selected", "Please search and select an item first.")
            return

        item_no = self.selected_stock_in_item_data[0]
        try:
            quantity = int(self.stock_in_qty_entry.get())
            if quantity <= 0:
                messagebox.showwarning("Invalid Quantity", "Quantity must be a positive number.")
                return
        except ValueError:
            messagebox.showwarning("Input Error", "Please enter a valid number for quantity.")
            return

        supplier = self.stock_in_supplier_entry.get().strip()
        if not supplier:
            messagebox.showwarning("Input Error", "Supplier name is required.")
            return
        
        # Date is automatically current timestamp
        date_received = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if self.db.record_stock_in(item_no, quantity, date_received, supplier): # Pass the automatically generated date
            messagebox.showinfo("Success", "Stock In recorded successfully!")
            self.refresh_stock_in_log()
            self.refresh_inventory_list() # Update inventory view
            self.stock_in_search_entry.delete(0, tk.END)
            self.stock_in_results_tree.delete(*self.stock_in_results_tree.get_children()) # Clear treeview
            self.stock_in_qty_entry.delete(0, tk.END)
            self.stock_in_supplier_entry.delete(0, tk.END)
            self.selected_stock_in_item_data = None
        else:
                messagebox.showerror("Error", "Failed to record Stock In.")

    def refresh_stock_in_log(self):
        """Refreshes the stock in log treeview."""
        for i in self.stock_in_tree.get_children():
            self.stock_in_tree.delete(i)
        logs = self.db.get_all_stock_in_logs()
        for log in logs:
            # log: (stock_in_id, item_no, item_name, item_description, quantity, date_received, supplier, supplier_price)
            date_from_db = log[5] # This is the string from the DB
            # We now expect only '%Y-%m-%d %H:%M:%S' format for date_received
            display_date = ""
            try:
                display_date = datetime.strptime(date_from_db, '%Y-%m-%d %H:%M:%S').strftime('%d-%b-%Y')
            except ValueError:
                display_date = "Invalid Date" # Fallback if format is unexpected
            
            self.stock_in_tree.insert("", "end", values=(
                log[1], log[2], log[3], log[4], display_date, log[6], f"₱{log[7]:.2f}"
            ))

    # --- Stock Out Log (Sales) Tab ---
    def create_stock_out_tab(self):
        self.stock_out_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.stock_out_frame, text="Sales Log")
        self.stock_out_frame.columnconfigure(0, weight=1)
        self.stock_out_frame.rowconfigure(0, weight=1)

        self.sales_tree = ttk.Treeview(self.stock_out_frame, columns=(
            'Sale ID', 'Date', 'Total Amount', 'Payment Type', 'Customer Name', 'Paid Amount', 'Status', 'Additional Charge'
        ), show='headings')
        self.sales_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        cols = ['Sale ID', 'Date', 'Total Amount', 'Payment Type', 'Customer Name', 'Paid Amount', 'Status', 'Additional Charge']
        widths = [80, 150, 100, 100, 150, 100, 80, 120] # Adjusted width for Sale ID and added Additional Charge
        for col, width in zip(cols, widths):
            self.sales_tree.heading(col, text=col)
            self.sales_tree.column(col, width=width, anchor="center")
        self.sales_tree.column('Customer Name', anchor="w")

        scrollbar = ttk.Scrollbar(self.stock_out_frame, orient="vertical", command=self.sales_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=10)
        self.sales_tree.configure(yscrollcommand=scrollbar.set)

        ttk.Button(self.stock_out_frame, text="View Sale Details", command=self.view_sale_details).grid(row=1, column=0, pady=10, sticky="e")
        # Bind the TreeviewSelect event to automatically update selection for view details
        self.sales_tree.bind("<<TreeviewSelect>>", self.on_sales_tree_select)
        self.selected_sales_log_item = None # To store the selected item from the Sales Log Treeview

        self.refresh_sales_log()

    def on_sales_tree_select(self, event):
        """Updates the selected item for the Sales Log tab when a row is clicked."""
        selected_items = self.sales_tree.selection()
        if selected_items:
            self.selected_sales_log_item = selected_items[0]
        else:
            self.selected_sales_log_item = None

    def refresh_sales_log(self):
        """Refreshes the sales log treeview."""
        for i in self.sales_tree.get_children():
            self.sales_tree.delete(i)
        sales = self.db.get_all_sales() # This now orders by sale_id ASC
        for sale in sales:
            # sale: (sale_id, sale_date, total_amount, payment_type, customer_name, paid_amount, status, additional_charge)
            sale_id_formatted = f"{sale[0]:06d}" # Format Sale ID with leading zeros
            # Format date for display
            display_date = datetime.strptime(sale[1], '%Y-%m-%d %H:%M:%S').strftime('%d-%b-%Y %H:%M:%S')
            self.sales_tree.insert("", "end", values=(
                sale_id_formatted, display_date, f"₱{sale[2]:.2f}", sale[3], sale[4] or "N/A", f"₱{sale[5]:.2f}", sale[6], f"₱{sale[7]:.2f}"
            ))
            # Tag unpaid/partially paid credit sales for visual cue
            if sale[3] == 'Credit' and sale[6] != 'Paid':
                self.sales_tree.item(self.sales_tree.get_children()[-1], tags=('credit_sale',))
        self.sales_tree.tag_configure('credit_sale', background='#FFF2CC') # Light yellow for credit sales

    def view_sale_details(self):
        """Displays details of a selected sale."""
        selected_item = self.sales_tree.selection() # Use selection() directly for the button click
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a sale to view details.")
            return

        # Get the raw sale_id string from the treeview. This might be "3" or "000003".
        sale_id_raw_from_tree = self.sales_tree.item(selected_item[0])['values'][0]
        
        # Convert it to an integer. This will convert "000003" to 3, or "3" to 3.
        sale_id_int = int(sale_id_raw_from_tree) 
        
        # Re-format the integer back to a string with leading zeros for consistent display.
        sale_id_display_formatted = f"{sale_id_int:06d}"

        sale_summary, sale_items = self.db.get_sale_details_for_display(sale_id_int) # Use the integer ID for DB query

        if not sale_summary:
            messagebox.showerror("Error", "Could not retrieve sale details.")
            return

        total_amount, additional_charge = sale_summary

        detail_window = tk.Toplevel(self)
        # Use the re-formatted string for the window title
        detail_window.title(f"Sale Details (ID: {sale_id_display_formatted})")
        detail_window.geometry("650x400") # Increased size for more columns
        detail_window.transient(self)

        ttk.Label(detail_window, text=f"Items for Sale ID: {sale_id_display_formatted}", font=("Arial", 12, "bold")).pack(pady=5)
        ttk.Label(detail_window, text=f"Total Sale Amount: ₱{total_amount:.2f}", font=("Arial", 10)).pack(pady=2)
        ttk.Label(detail_window, text=f"Additional Charge: ₱{additional_charge:.2f}", font=("Arial", 10)).pack(pady=2)

        # Create a frame to hold the Treeview and its scrollbar
        tree_container_frame = ttk.Frame(detail_window)
        tree_container_frame.pack(fill="both", expand=True, padx=10, pady=5) # Use pack for this frame

        details_tree = ttk.Treeview(tree_container_frame, columns=(
            'Item No.', 'Item Name', 'Description', 'Quantity', 'Price at Sale', 'Subtotal'
        ), show='headings')
        details_tree.pack(side="left", fill="both", expand=True) # Pack left within the container

        cols = ['Item No.', 'Item Name', 'Description', 'Quantity', 'Price at Sale', 'Subtotal']
        widths = [80, 150, 200, 80, 100, 100]
        for col, width in zip(cols, widths):
            details_tree.heading(col, text=col)
            details_tree.column(col, width=width, anchor="center")
        details_tree.column('Item Name', anchor="w")
        details_tree.column('Description', anchor="w")


        for item in sale_items:
            # item: (item_no, item_name, item_description, quantity, price_at_sale, subtotal)
            details_tree.insert("", "end", values=(
                item[0], item[1], item[2], item[3], f"₱{item[4]:.2f}", f"₱{item[5]:.2f}"
            ))

        scrollbar = ttk.Scrollbar(tree_container_frame, orient="vertical", command=details_tree.yview)
        scrollbar.pack(side="right", fill="y") # Pack right within the container
        details_tree.configure(yscrollcommand=scrollbar.set)

    # --- Credit Sales Tab ---
    def create_credit_sales_tab(self):
        self.credit_sales_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.credit_sales_frame, text="Credit Sales")
        self.credit_sales_frame.columnconfigure(0, weight=1)
        self.credit_sales_frame.rowconfigure(0, weight=1)

        self.credit_sales_tree = ttk.Treeview(self.credit_sales_frame, columns=(
            'Sale ID', 'Date', 'Customer Name', 'Total Amount', 'Paid Amount', 'Balance', 'Status'
        ), show='headings')
        self.credit_sales_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        cols = ['Sale ID', 'Date', 'Customer Name', 'Total Amount', 'Paid Amount', 'Balance', 'Status']
        widths = [70, 150, 180, 100, 100, 100, 80]
        for col, width in zip(cols, widths):
            self.credit_sales_tree.heading(col, text=col)
            self.credit_sales_tree.column(col, width=width, anchor="center")
        self.credit_sales_tree.column('Customer Name', anchor="w")

        scrollbar = ttk.Scrollbar(self.credit_sales_frame, orient="vertical", command=self.credit_sales_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=10)
        self.credit_sales_tree.configure(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(self.credit_sales_frame)
        button_frame.grid(row=1, column=0, sticky="ew", pady=10)
        button_frame.columnconfigure(0, weight=1) # Center buttons

        ttk.Button(button_frame, text="Record Payment", command=self.record_credit_payment).pack(side="left", padx=5)
        ttk.Button(button_frame, text="View Details", command=self.view_credit_sale_details).pack(side="left", padx=5) # Separate function for Credit Sales view details

        self.refresh_credit_sales_list()

    def refresh_credit_sales_list(self):
        """Refreshes the credit sales treeview."""
        for i in self.credit_sales_tree.get_children():
            self.credit_sales_tree.delete(i)
        credit_sales = self.db.get_credit_sales()
        for sale in credit_sales:
            sale_id, sale_date, total_amount, payment_type, customer_name, paid_amount, status, _ = sale # Added '_' for additional_charge
            balance = total_amount - paid_amount
            # Format Sale ID with leading zeros
            sale_id_formatted = f"{sale_id:06d}"
            # Format date for display
            display_date = datetime.strptime(sale_date, '%Y-%m-%d %H:%M:%S').strftime('%d-%b-%Y %H:%M:%S')
            self.credit_sales_tree.insert("", "end", values=(
                sale_id_formatted, display_date, customer_name, f"₱{total_amount:.2f}", f"₱{paid_amount:.2f}",
                f"₱{balance:.2f}", status
            ), tags=('unpaid' if status != 'Paid' else 'paid'))
        self.credit_sales_tree.tag_configure('unpaid', background='#FFCCCC') # Light red for unpaid/partially paid
        self.credit_sales_tree.tag_configure('paid', background='#CCFFCC') # Light green for paid

    def record_credit_payment(self):
        """Opens a window to record payment for a credit sale."""
        selected_item = self.credit_sales_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a credit sale to record payment.")
            return

        sale_values = self.credit_sales_tree.item(selected_item[0])['values']
        sale_id = sale_values[0]
        # Remove '₱' and convert to float
        # Convert formatted sale_id back to int for database lookup
        sale_id_int = int(sale_id)
        total_amount = float(str(sale_values[3]).replace('₱', ''))
        paid_amount_so_far = float(str(sale_values[4]).replace('₱', '').replace('#', '')) # Handle '#' for consistency
        current_balance = float(str(sale_values[5]).replace('₱', ''))

        if current_balance <= 0:
            messagebox.showinfo("Already Paid", "This credit sale is already fully paid.")
            return

        payment_window = tk.Toplevel(self)
        payment_window.title(f"Record Payment for Sale ID: {sale_id}")
        payment_window.geometry("350x200")
        payment_window.transient(self)

        ttk.Label(payment_window, text=f"Total Amount: ₱{total_amount:.2f}").pack(pady=5)
        ttk.Label(payment_window, text=f"Paid So Far: ₱{paid_amount_so_far:.2f}").pack(pady=5)
        ttk.Label(payment_window, text=f"Remaining Balance: ₱{current_balance:.2f}").pack(pady=5)

        ttk.Label(payment_window, text="Amount to Pay:").pack(pady=5)
        amount_entry = ttk.Entry(payment_window, width=30)
        amount_entry.pack(pady=5)
        amount_entry.insert(0, f"{current_balance:.2f}") # Suggest full balance

        def process_payment():
            try:
                payment_amount = float(amount_entry.get())
                if payment_amount <= 0:
                    messagebox.showwarning("Invalid Amount", "Payment amount must be positive.")
                    return
                # Allow overpayment to be handled by the database logic
                # if payment_amount > current_balance:
                #     messagebox.showwarning("Overpayment", "Payment amount exceeds remaining balance.")
                #     return
            except ValueError:
                messagebox.showwarning("Input Error", "Please enter a valid number for payment amount.")
                return

            if self.db.update_credit_sale_payment(sale_id_int, payment_amount): # Use sale_id_int here
                messagebox.showinfo("Success", "Payment recorded successfully!")
                self.refresh_credit_sales_list()
                self.refresh_sales_log() # Also update the main sales log
                payment_window.destroy()
            else:
                messagebox.showerror("Error", "Failed to record payment.")

        ttk.Button(payment_window, text="Submit Payment", command=process_payment).pack(pady=10)

    def view_credit_sale_details(self):
        """Displays details of a selected credit sale. Separate function from main sales log."""
        selected_item = self.credit_sales_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a credit sale to view details.")
            return

        sale_id_raw_from_tree = self.credit_sales_tree.item(selected_item[0])['values'][0]
        sale_id_int = int(sale_id_raw_from_tree)
        sale_id_display_formatted = f"{sale_id_int:06d}"

        sale_summary, sale_items = self.db.get_sale_details_for_display(sale_id_int)

        if not sale_summary:
            messagebox.showerror("Error", "Could not retrieve sale details.")
            return

        total_amount, additional_charge = sale_summary

        detail_window = tk.Toplevel(self)
        detail_window.title(f"Credit Sale Details (ID: {sale_id_display_formatted})")
        detail_window.geometry("650x400")
        detail_window.transient(self)

        ttk.Label(detail_window, text=f"Items for Credit Sale ID: {sale_id_display_formatted}", font=("Arial", 12, "bold")).pack(pady=5)
        ttk.Label(detail_window, text=f"Total Credit Sale Amount: ₱{total_amount:.2f}", font=("Arial", 10)).pack(pady=2)
        ttk.Label(detail_window, text=f"Additional Charge: ₱{additional_charge:.2f}", font=("Arial", 10)).pack(pady=2)

        # Create a frame to hold the Treeview and its scrollbar
        tree_container_frame = ttk.Frame(detail_window)
        tree_container_frame.pack(fill="both", expand=True, padx=10, pady=5) # Use pack for this frame

        details_tree = ttk.Treeview(tree_container_frame, columns=(
            'Item No.', 'Item Name', 'Description', 'Quantity', 'Price at Sale', 'Subtotal'
        ), show='headings')
        details_tree.pack(side="left", fill="both", expand=True) # Pack left within the container

        cols = ['Item No.', 'Item Name', 'Description', 'Quantity', 'Price at Sale', 'Subtotal']
        widths = [80, 150, 200, 80, 100, 100]
        for col, width in zip(cols, widths):
            details_tree.heading(col, text=col)
            details_tree.column(col, width=width, anchor="center")
        details_tree.column('Item Name', anchor="w")
        details_tree.column('Description', anchor="w")

        for item in sale_items:
            details_tree.insert("", "end", values=(
                item[0], item[1], item[2], item[3], f"₱{item[4]:.2f}"
            ))

        scrollbar = ttk.Scrollbar(tree_container_frame, orient="vertical", command=details_tree.yview)
        scrollbar.pack(side="right", fill="y") # Pack right within the container
        details_tree.configure(yscrollcommand=scrollbar.set)


    # --- Profit & Expenses Tab ---
    def create_profit_expenses_tab(self):
        self.profit_expenses_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.profit_expenses_frame, text="Profit & Expenses")
        self.profit_expenses_frame.columnconfigure(0, weight=1) # For expense form/controls
        self.profit_expenses_frame.columnconfigure(1, weight=1) # For financial summary
        self.profit_expenses_frame.rowconfigure(1, weight=1) # For expenses treeview

        # --- Expense Input Form ---
        self.expense_input_frame = ttk.LabelFrame(self.profit_expenses_frame, text="Expense Details", padding="10")
        self.expense_input_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.expense_input_frame.columnconfigure(1, weight=1) # Make entry fields expand

        ttk.Label(self.expense_input_frame, text="Item Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.expense_item_name_entry = ttk.Entry(self.expense_input_frame, width=40)
        self.expense_item_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(self.expense_input_frame, text="Description:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.expense_description_entry = ttk.Entry(self.expense_input_frame, width=40)
        self.expense_description_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(self.expense_input_frame, text="Amount:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.expense_amount_entry = ttk.Entry(self.expense_input_frame, width=40)
        self.expense_amount_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Buttons for Add, Update, Delete and Clear
        expense_action_buttons_frame = ttk.Frame(self.expense_input_frame)
        expense_action_buttons_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.add_expense_btn = ttk.Button(expense_action_buttons_frame, text="Add Expense", command=self.add_expense_entry)
        self.add_expense_btn.pack(side="left", padx=5)

        self.update_expense_btn = ttk.Button(expense_action_buttons_frame, text="Update Expense", command=self.update_expense_entry, state="disabled")
        self.update_expense_btn.pack(side="left", padx=5)
        
        # Renamed from "Delete Selected Expense" to "Delete Expense"
        self.delete_expense_btn = ttk.Button(expense_action_buttons_frame, text="Delete Expense", command=self.delete_selected_expense, state="disabled")
        self.delete_expense_btn.pack(side="left", padx=5)

        self.clear_expense_form_btn = ttk.Button(expense_action_buttons_frame, text="Clear Form", command=self.clear_expense_form)
        self.clear_expense_form_btn.pack(side="left", padx=5)


        # Profit Summary
        profit_summary_frame = ttk.LabelFrame(self.profit_expenses_frame, text="Financial Summary", padding="10")
        profit_summary_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        profit_summary_frame.columnconfigure(0, weight=1)
        profit_summary_frame.columnconfigure(1, weight=1)

        self.total_sales_lbl = ttk.Label(profit_summary_frame, text="Total Sales (Today): ₱0.00", font=("Arial", 12))
        self.total_sales_lbl.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.total_cogs_lbl = ttk.Label(profit_summary_frame, text="Total COGS (Today): ₱0.00", font=("Arial", 12))
        self.total_cogs_lbl.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.gross_profit_lbl = ttk.Label(profit_summary_frame, text="Gross Profit (Today): ₱0.00", font=("Arial", 12, "bold"))
        self.gross_profit_lbl.grid(row=2, column=0, padx=5, pady=2, sticky="w")

        self.total_expenses_lbl = ttk.Label(profit_summary_frame, text="Total Expenses (Today): ₱0.00", font=("Arial", 12))
        self.total_expenses_lbl.grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.net_income_lbl = ttk.Label(profit_summary_frame, text="Net Income (Today): ₱0.00", font=("Arial", 14, "bold"), foreground="green")
        self.net_income_lbl.grid(row=4, column=0, padx=5, pady=2, sticky="w")

        # Expenses Log Treeview
        self.expenses_tree = ttk.Treeview(self.profit_expenses_frame, columns=(
            'Expense No.', 'Date', 'Item Name', 'Name', 'Amount'
        ), show='headings')
        self.expenses_tree.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

        cols = ['Expense No.', 'Date', 'Item Name', 'Name', 'Amount']
        widths = [80, 150, 150, 250, 100]
        for col, width in zip(cols, widths):
            self.expenses_tree.heading(col, text=col)
            self.expenses_tree.column(col, width=width, anchor="center")
        self.expenses_tree.column('Item Name', anchor="w")
        self.expenses_tree.column('Name', anchor="w")

        scrollbar = ttk.Scrollbar(self.profit_expenses_frame, orient="vertical", command=self.expenses_tree.yview)
        scrollbar.grid(row=1, column=2, sticky="ns", pady=10)
        self.expenses_tree.configure(yscrollcommand=scrollbar.set)

        self.expenses_tree.bind("<<TreeviewSelect>>", self.on_expense_tree_select)

        self.selected_expense_id = None # To track the expense being edited

        self.refresh_expenses_list()
        self.refresh_profit_summary()
        self.clear_expense_form() # Initial state: form clear, update/delete buttons disabled

    def add_expense_entry(self):
        """Adds a new expense using the current form inputs."""
        item_name = self.expense_item_name_entry.get().strip()
        description = self.expense_description_entry.get().strip()
        
        try:
            amount = float(self.expense_amount_entry.get())
            if amount <= 0:
                messagebox.showwarning("Invalid Amount", "Expense Amount must be positive.")
                return
        except ValueError:
            # Changed error message as per user's request
            messagebox.showwarning("Input Error", "Expense Amount is blank or invalid.")
            return

        if not description and not item_name:
            messagebox.showwarning("Input Error", "Item Name or Description is required for the expense.")
            return

        data = {
            'expense_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'item_name': item_name,
            'description': description,
            'amount': amount
        }

        if self.db.add_expense(data):
            messagebox.showinfo("Success", "Expense added successfully!")
            self.clear_expense_form()
            self.refresh_expenses_list()
            self.refresh_profit_summary()
        else:
            messagebox.showerror("Error", "Failed to add expense.")

    def update_expense_entry(self):
        """Updates an existing expense using the current form inputs and selected_expense_id."""
        if not self.selected_expense_id:
            messagebox.showwarning("No Expense Selected", "Please select an expense to update.")
            return

        item_name = self.expense_item_name_entry.get().strip()
        description = self.expense_description_entry.get().strip()
        
        try:
            amount = float(self.expense_amount_entry.get())
            if amount <= 0:
                messagebox.showwarning("Invalid Amount", "Expense Amount must be positive.")
                return
        except ValueError:
            # Changed error message as per user's request
            messagebox.showwarning("Input Error", "Expense Amount is blank or invalid.")
            return

        if not description and not item_name:
            messagebox.showwarning("Input Error", "Item Name or Description is required for the expense.")
            return

        data = {
            'expense_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # Update timestamp or keep original? For now, update.
            'item_name': item_name,
            'description': description,
            'amount': amount
        }

        if self.db.update_expense(self.selected_expense_id, data):
            messagebox.showinfo("Success", "Expense updated successfully!")
            self.clear_expense_form()
            self.refresh_expenses_list()
            self.refresh_profit_summary()
        else:
            messagebox.showerror("Error", "Failed to update expense.")

    def edit_selected_expense_form_populate(self):
        """Populates the expense input fields with the selected expense's data for editing."""
        selected_item = self.expenses_tree.selection()
        if not selected_item:
            # This case should ideally not be reached if button state is managed correctly,
            # but it's good for robustness.
            messagebox.showwarning("No Selection", "Please select an expense to edit.")
            return
        
        # Get the expense_id from the first column of the selected row's values
        expense_id_str = self.expenses_tree.item(selected_item[0])['values'][0]
        expense_id = int(expense_id_str) # Convert formatted string back to int

        expense_data = self.db.get_expense_by_id(expense_id)
        if expense_data:
            self.selected_expense_id = expense_data[0] # Store the actual ID for update
            self.expense_item_name_entry.delete(0, tk.END)
            self.expense_item_name_entry.insert(0, str(expense_data[2]) if expense_data[2] is not None else '')
            self.expense_description_entry.delete(0, tk.END)
            self.expense_description_entry.insert(0, str(expense_data[3]) if expense_data[3] is not None else '')
            self.expense_amount_entry.delete(0, tk.END)
            self.expense_amount_entry.insert(0, str(expense_data[4]) if expense_data[4] is not None else '')
            
            # Enable update and delete buttons when an item is selected for editing
            self.update_expense_btn.config(state="normal")
            self.delete_expense_btn.config(state="normal")
            self.add_expense_btn.config(state="disabled") # Disable add button while editing
        else:
            messagebox.showerror("Error", "Could not retrieve expense data for editing.")
            self.clear_expense_form() # Clear form if data retrieval fails

    def delete_selected_expense(self):
        """Deletes the selected expense from the database."""
        selected_item = self.expenses_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select an expense to delete.")
            return
        
        # Get the expense_id string directly from the treeview, which should be formatted
        expense_id_from_treeview = self.expenses_tree.item(selected_item[0])['values'][0]
        
        # Convert it to an integer for the database operation
        expense_id_for_db = int(expense_id_from_treeview)
        
        # Re-format the integer back to the 6-digit string for display in the message
        display_expense_no = f"{expense_id_for_db:06d}"

        # Updated confirmation message to show "Expense No." with 6-digit format
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Expense No. '{display_expense_no}'?"):
            if self.db.delete_expense(expense_id_for_db): # Use the integer ID for database operation
                messagebox.showinfo("Success", "Expense deleted successfully!")
                self.clear_expense_form() # Clear form and reset buttons
                self.refresh_expenses_list()
                self.refresh_profit_summary()
            else:
                messagebox.showerror("Error", "Failed to delete expense.")

    def clear_expense_form(self):
        """Clears the expense input fields and resets button states."""
        self.expense_item_name_entry.delete(0, tk.END)
        self.expense_description_entry.delete(0, tk.END)
        self.expense_amount_entry.delete(0, tk.END)
        self.selected_expense_id = None # Clear selected ID
        
        # Reset button states
        self.add_expense_btn.config(state="normal")
        self.update_expense_btn.config(state="disabled")
        self.delete_expense_btn.config(state="disabled") # Disabled as nothing is selected for deleting

        # Deselect any item in treeview to reflect cleared state
        self.expenses_tree.selection_remove(self.expenses_tree.selection())


    def on_expense_tree_select(self, event):
        """Called when an item in the expenses treeview is selected. Populates the form for editing."""
        selected_item = self.expenses_tree.selection()
        if selected_item:
            # When an item is selected, enable the update and delete buttons
            self.edit_selected_expense_form_populate() # This will populate the form and enable buttons
        else:
            # If nothing is selected, clear the form and disable update/delete buttons
            self.clear_expense_form()

    def refresh_expenses_list(self):
        """Refreshes the expenses log treeview."""
        for i in self.expenses_tree.get_children():
            self.expenses_tree.delete(i)
        expenses = self.db.get_all_expenses() # Now fetches item_name as well
        for expense in expenses:
            # expense: (expense_id, expense_date, item_name, description, amount)
            expense_id_formatted = f"{expense[0]:06d}" # Format ID with leading zeros
            # Format date for display
            display_date = datetime.strptime(expense[1], '%Y-%m-%d %H:%M:%S').strftime('%d-%b-%Y %H:%M:%S')
            self.expenses_tree.insert("", "end", values=(
                expense_id_formatted, display_date, expense[2], expense[3], f"₱{expense[4]:.2f}"
            ))

    def refresh_profit_summary(self):
        """Refreshes the profit and expense summary section."""
        today = datetime.now()
        
        # Daily
        start_of_day = f"{today.strftime('%Y-%m-%d')} 00:00:00"
        end_of_day = f"{today.strftime('%Y-%m-%d')} 23:59:59"
        total_revenue_today, cogs_selling_price_based_today, cogs_supplier_price_based_today = self.db.get_sales_summary(start_of_day, end_of_day)
        gross_profit_today = total_revenue_today - cogs_selling_price_based_today # Gross profit based on current COGS (selling price based)
        total_expenses_today = self.db.get_total_expenses(start_of_day, end_of_day)
        net_income_today = gross_profit_today - total_expenses_today

        self.daily_sales_lbl.config(text=f"₱{total_revenue_today:.2f}")
        self.daily_profit_lbl.config(text=f"₱{net_income_today:.2f}")

        # Weekly (Sunday to Saturday)
        # Calculate the start of the week (Sunday)
        start_of_week = today - timedelta(days=(today.weekday() + 1) % 7)
        start_of_week_str = start_of_week.strftime('%Y-%m-%d 00:00:00') # Converted to string here
        end_of_week_str = (start_of_week + timedelta(days=6)).strftime('%Y-%m-%d 23:59:59') # Converted to string here
        
        total_revenue_week, cogs_selling_price_based_week, cogs_supplier_price_based_week = self.db.get_sales_summary(start_of_week_str, end_of_week_str)
        gross_profit_week = total_revenue_week - cogs_selling_price_based_week
        total_expenses_week = self.db.get_total_expenses(start_of_week_str, end_of_week_str)
        net_income_week = gross_profit_week - total_expenses_week

        self.weekly_sales_lbl.config(text=f"₱{total_revenue_week:.2f}")
        self.weekly_profit_lbl.config(text=f"₱{net_income_week:.2f}")

        # Monthly
        start_of_month = today.replace(day=1)
        start_date_db_format = start_of_month.strftime('%Y-%m-%d 00:00:00')
        
        # Calculate the last day of the current month
        last_day_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        end_date_db_format = last_day_of_month.strftime('%Y-%m-%d 23:59:59')
        
        total_revenue_month, cogs_selling_price_based_month, cogs_supplier_price_based_month = self.db.get_sales_summary(start_date_db_format, end_date_db_format)
        gross_profit_month = total_revenue_month - cogs_selling_price_based_month
        total_expenses_month = self.db.get_total_expenses(start_date_db_format, end_date_db_format)
        net_income_month = gross_profit_month - total_expenses_month

        self.monthly_sales_lbl.config(text=f"₱{total_revenue_month:.2f}")
        self.monthly_profit_lbl.config(text=f"₱{net_income_month:.2f}")


        # Dashboard Summary specific labels (from Profit & Expenses tab's summary)
        self.total_sales_lbl.config(text=f"Total Sales (Today): ₱{total_revenue_today:.2f}")
        self.total_cogs_lbl.config(text=f"Total COGS (Today): ₱{cogs_selling_price_based_today:.2f}")
        self.gross_profit_lbl.config(text=f"Gross Profit (Today): ₱{gross_profit_today:.2f}")
        self.total_expenses_lbl.config(text=f"Total Expenses (Today): ₱{total_expenses_today:.2f}")
        self.net_income_lbl.config(text=f"Net Income (Today): ₱{net_income_today:.2f}")

        # Update color for net income
        if net_income_today < 0:
            self.net_income_lbl.config(foreground="red")
        else:
            self.net_income_lbl.config(foreground="green")

    # --- Pricing Tab ---
    def create_pricing_tab(self):
        self.pricing_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.pricing_frame, text="Pricing")
        self.pricing_frame.columnconfigure(0, weight=1)
        self.pricing_frame.rowconfigure(1, weight=1) # Row for Treeview

        # Pricing Control Frame (Add/Delete buttons)
        pricing_control_frame = ttk.Frame(self.pricing_frame, padding="10")
        pricing_control_frame.grid(row=0, column=0, sticky="ew", pady=5)
        pricing_control_frame.columnconfigure(0, weight=1) # Pushes buttons to the right

        ttk.Button(pricing_control_frame, text="Add Item", command=self.open_add_edit_item_window).pack(side="right", padx=5)
        # Added Edit Item button to Pricing tab
        ttk.Button(pricing_control_frame, text="Edit Item", command=self.edit_selected_pricing_item).pack(side="right", padx=5)
        ttk.Button(pricing_control_frame, text="Delete Item", command=self.delete_selected_pricing_item).pack(side="right", padx=5)


        # Pricing Treeview
        self.pricing_tree = ttk.Treeview(self.pricing_frame, columns=(
            'Item No.', 'Item Name', 'Item Description', 'Supplier Price (Investment)', 'Volume',
            'Supplier Price (Per Unit)', 'Interest', 'Suggested Price', 'Selling Price'
        ), show='headings')
        self.pricing_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=10) # Changed row to 1

        # Define column headings and widths exactly as per the image
        cols = [
            'Item No.', 'Item Name', 'Item Description', 'Supplier Price (Investment)', 'Volume',
            'Supplier Price (Per Unit)', 'Interest', 'Suggested Price', 'Selling Price'
        ]
        widths = [80, 150, 200, 120, 70, 120, 80, 120, 120] # Adjusted width for Interest

        for col, width in zip(cols, widths):
            self.pricing_tree.heading(col, text=col)
            self.pricing_tree.column(col, width=width, anchor="center")
        
        # Specific alignments as per image and logical data type
        self.pricing_tree.column('Item Name', anchor="w")
        self.pricing_tree.column('Item Description', anchor="w")
        self.pricing_tree.column('Supplier Price (Investment)', anchor="e")
        self.pricing_tree.column('Volume', anchor="center") # Volume is an integer
        self.pricing_tree.column('Supplier Price (Per Unit)', anchor="e")
        self.pricing_tree.column('Interest', anchor="e") # Interest is an integer
        self.pricing_tree.column('Suggested Price', anchor="e")
        self.pricing_tree.column('Selling Price', anchor="e")


        scrollbar = ttk.Scrollbar(self.pricing_frame, orient="vertical", command=self.pricing_tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=10) # Changed row to 1
        self.pricing_tree.configure(yscrollcommand=scrollbar.set)

        # Only allow inline editing for 'Selling Price'
        self.pricing_tree.bind("<Double-1>", self._on_pricing_tree_double_click) 

        self.refresh_pricing_list() # Initial load

    def _on_pricing_tree_double_click(self, event):
        """Handle double-click event on the pricing treeview for editing specific columns."""
        region = self.pricing_tree.identify("region", event.x, event.y)
        if region == "heading":
            return # Don't edit headings

        column = self.pricing_tree.identify_column(event.x)
        column_text = self.pricing_tree.heading(column, "text")
        item_id = self.pricing_tree.identify_row(event.y)
        if not item_id:
            return

        # Double-click editing is now only for 'Selling Price'
        if column_text == 'Selling Price':
            x, y, width, height = self.pricing_tree.bbox(item_id, column)
            item_no = self.pricing_tree.item(item_id)['values'][0]
            current_value_str = self.pricing_tree.set(item_id, column)
            current_value = current_value_str.replace('₱', '').strip()

            entry_edit = ttk.Entry(self.pricing_tree)
            entry_edit.place(x=x, y=y, width=width, height=height)
            entry_edit.insert(0, current_value)
            entry_edit.focus_set()

            def save_selling_price_edit(event=None):
                new_value = entry_edit.get().strip()
                try:
                    new_selling_price = float(new_value)
                    if new_selling_price < 0:
                        messagebox.showwarning("Input Error", "Selling Price cannot be negative.")
                        return
                    # Update the database
                    item_data = self.db.get_item_by_item_no(item_no)
                    if item_data:
                        # Unpack current data (assuming 11 fields)
                        _, item_name, desc, unit, sup_price, _, stock, reorder_lvl, reorder_qty, volume, interest = item_data
                        updated_data = {
                            'item_name': item_name, 'item_description': desc, 'unit': unit,
                            'supplier_price': sup_price, 'selling_price': new_selling_price,
                            'current_stock': stock, 'reorder_level': reorder_lvl,
                            'reorder_qty': reorder_qty, 'volume': volume, 'interest': interest
                        }
                        if self.db.update_item(item_no, updated_data):
                            self.refresh_pricing_list()
                            self.refresh_inventory_list() # Also refresh inventory as it shows selling price
                        else:
                            messagebox.showerror("Update Error", "Failed to update selling price in database.")
                    else:
                        messagebox.showerror("Error", "Item not found in database.")
                except ValueError:
                    messagebox.showwarning("Input Error", "Please enter a valid number for selling price.")
                finally:
                    entry_edit.destroy()

            entry_edit.bind("<Return>", save_selling_price_edit)
            entry_edit.bind("<FocusOut>", save_selling_price_edit)


    def edit_selected_pricing_item(self):
        """Opens the add/edit window pre-filled with selected item's data from the Pricing tab."""
        selected_item = self.pricing_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select an item to edit.")
            return
        # Get the item_no from the first column of the selected item in the pricing tree.
        # This is safe because 'Item No.' is always the first column in the pricing_tree.
        item_no = self.pricing_tree.item(selected_item[0])['values'][0]
        item_data = self.db.get_item_by_item_no(item_no)
        if item_data:
            self.open_add_edit_item_window(item_data)

    def delete_selected_pricing_item(self):
        """Deletes the selected inventory item from the pricing tab."""
        selected_item = self.pricing_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select an item to delete.")
            return
        item_no = self.pricing_tree.item(selected_item[0])['values'][0]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete item '{item_no}' and all its associated data (inventory, sales logs etc.)?"):
            if self.db.delete_item(item_no):
                messagebox.showinfo("Success", "Item and its pricing deleted successfully!")
                self.refresh_inventory_list() # Refresh inventory tab
                self.refresh_pricing_list() # Refresh pricing tab
                self.refresh_pos_search_results() # Refresh POS search results
            else:
                messagebox.showerror("Error", "Failed to delete item.")

    def refresh_pricing_list(self):
        """Calculates and populates the pricing tab with suggested prices."""
        for i in self.pricing_tree.get_children():
            self.pricing_tree.delete(i)

        all_items = self.db.get_all_items() # This now includes 'volume' (idx 9) and 'interest' (idx 10)

        for item in all_items:
            # Unpack all 11 fields, including volume and interest
            item_no, item_name, desc, unit, supplier_price_investment, current_selling_price, stock, reorder_lvl, reorder_qty, volume, item_interest = item

            # Ensure numeric values are valid, default if None or invalid
            supplier_price_investment = float(supplier_price_investment) if supplier_price_investment is not None else 0.0
            volume = int(volume) if volume is not None else 1
            item_interest = int(item_interest) if item_interest is not None else 0 # Ensure interest is an integer

            # Ensure volume is at least 1 to prevent division by zero
            volume = max(1, volume)

            # Calculations
            supplier_price_per_unit = supplier_price_investment / volume if volume > 0 else 0.0
            
            # Interest is now a direct amount to add
            suggested_price = supplier_price_per_unit + item_interest
            
            # Selling Price is rounded up
            selling_price_rounded_up = math.ceil(suggested_price)

            # Volume should always show '1' if the value is 1, not empty string.
            volume_display = str(volume) 

            self.pricing_tree.insert("", "end", values=(
                item_no,
                item_name,
                desc,
                f"₱{supplier_price_investment:.2f}",
                volume_display, # Use volume_display, which now always shows '1' if volume is 1
                f"₱{supplier_price_per_unit:.2f}",
                item_interest, # Display as integer
                f"₱{suggested_price:.2f}",
                f"₱{selling_price_rounded_up:.2f}"
            ))
    
    def refresh_pos_search_results(self):
        """Refreshes the search results in the POS tab."""
        self.pos_search_items() # Simply re-call the search function with current query (or empty for all items)

    # --- Reports Tab ---
    def create_reports_tab(self):
        self.reports_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.reports_frame, text="Reports")
        self.reports_frame.columnconfigure(0, weight=1)
        self.reports_frame.rowconfigure(2, weight=1) # Reports output area

        # Report Type Selection
        report_control_frame = ttk.LabelFrame(self.reports_frame, text="Generate Reports", padding="10")
        report_control_frame.grid(row=0, column=0, sticky="ew", pady=5)
        report_control_frame.columnconfigure(1, weight=1)

        ttk.Label(report_control_frame, text="Report Type:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.report_type_var = tk.StringVar(value="Daily")
        ttk.OptionMenu(report_control_frame, self.report_type_var, "Daily", "Daily", "Weekly", "Monthly").grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Button(report_control_frame, text="Generate Report", command=self.generate_report).grid(row=0, column=2, padx=5, pady=5)

        # Report Output Area
        self.report_output_text = tk.Text(self.reports_frame, wrap="word", height=20, width=80)
        self.report_output_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        report_scrollbar = ttk.Scrollbar(self.reports_frame, orient="vertical", command=self.report_output_text.yview)
        report_scrollbar.grid(row=1, column=1, sticky="ns", pady=10)
        self.report_output_text.configure(yscrollcommand=report_scrollbar.set)

    def generate_report(self):
        """Generates and displays financial reports based on selected type."""
        report_type = self.report_type_var.get()
        self.report_output_text.delete(1.0, tk.END) # Clear previous report

        today = datetime.now()
        report_content = f"--- {report_type} Financial Report ---\n\n"

        # Initialize start_date and end_date outside the conditional blocks
        start_date_db_format = None
        end_date_db_format = None
        display_date_range = ""

        if report_type == "Daily":
            start_date_db_format = f"{today.strftime('%Y-%m-%d')} 00:00:00"
            end_date_db_format = f"{today.strftime('%Y-%m-%d')} 23:59:59"
            display_date_range = f"Date: {today.strftime('%d-%b-%Y')}\n"
        elif report_type == "Weekly":
            # Calculate the start of the week (Sunday)
            start_of_week = today - timedelta(days=(today.weekday() + 1) % 7)
            start_date_db_format = start_of_week.strftime('%Y-%m-%d 00:00:00')
            
            end_of_week = start_of_week + timedelta(days=6)
            end_date_db_format = end_of_week.strftime('%Y-%m-%d 23:59:59')
            
            display_date_range = f"Week: {start_of_week.strftime('%d-%b-%Y')} - {end_of_week.strftime('%d-%b-%Y')}\n"
        elif report_type == "Monthly":
            start_of_month = today.replace(day=1)
            start_date_db_format = start_of_month.strftime('%Y-%m-%d 00:00:00')
            
            # Calculate the last day of the current month
            last_day_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            end_date_db_format = last_day_of_month.strftime('%Y-%m-%d 23:59:59')
            
        # These lines will now always have start_date and end_date defined
        total_revenue, cogs_selling_price_based, cogs_supplier_price_based = self.db.get_sales_summary(start_date_db_format, end_date_db_format)
        total_expenses = self.db.get_total_expenses(start_date_db_format, end_date_db_format)

        gross_profit = total_revenue - cogs_selling_price_based
        net_income = gross_profit - total_expenses

        report_content += display_date_range
        report_content += f"\nTotal Sales (Collected): ₱{total_revenue:.2f}\n"
        report_content += f"Cost of Goods Sold (Selling Price Based): ₱{cogs_selling_price_based:.2f}\n" # Clarified COGS
        report_content += f"Cost of Goods Sold (Supplier Price Based): ₱{cogs_supplier_price_based:.2f}\n" # New COGS
        report_content += f"Gross Profit: ₱{gross_profit:.2f}\n"
        report_content += f"Total Expenses: ₱{total_expenses:.2f}\n"
        report_content += f"Net Income: ₱{net_income:.2f}\n"

        self.report_output_text.insert(tk.END, report_content)


if __name__ == "__main__":
    app = GroceryStoreApp()
    # Schedule the initial dashboard refresh to run after the mainloop starts
    app.after_idle(app._initial_dashboard_refresh)
    app.mainloop()
